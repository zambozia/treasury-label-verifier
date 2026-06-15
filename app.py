import time
import streamlit as st
import pandas as pd

from utils.csv_loader import load_csv
from utils.text_normalizer import normalize_text
from ocr.ocr_service import extract_text_from_image
from matching.record_matcher import find_best_record_match
from validation.validator import validate_label


def get_primary_issue(overall_status, match_result, validation_results):
    """
    Returns a short reviewer-friendly reason for the summary table.
    """
    if overall_status == "Pass":
        return "No issues detected"

    if overall_status == "Error":
        return match_result.get("notes", "Processing error")

    if match_result.get("status") == "No Match":
        return "No confident record match"

    if not validation_results:
        return "Validation not available"

    priority_order = [
        "Government Warning",
        "Alcohol Content",
        "Net Contents",
        "Brand Name",
        "Class / Type",
    ]

    problem_results = [
        result for result in validation_results
        if result.get("status") in ["Fail", "Missing", "Needs Review"]
    ]

    if not problem_results:
        return "Review recommended"

    for priority_field in priority_order:
        for result in problem_results:
            if result.get("field") == priority_field:
                return f'{result.get("field")}: {result.get("status")}'

    first_problem = problem_results[0]
    return f'{first_problem.get("field")}: {first_problem.get("status")}'


def build_field_issue_summary(validation_results):
    """
    Creates a compact summary of every validation issue for export/review.
    """
    if not validation_results:
        return ""

    issues = []

    for result in validation_results:
        if result.get("status") in ["Fail", "Missing", "Needs Review"]:
            issues.append(
                f'{result.get("field")}: {result.get("status")} - '
                f'{result.get("explanation")}'
            )

    if not issues:
        return "No issues detected"

    return " | ".join(issues)


def build_export_rows(detailed_results):
    """
    Flattens detailed validation results into one CSV-friendly table.
    """
    export_rows = []

    for item in detailed_results:
        match_result = item["match_result"]

        if item["validation_results"]:
            for result in item["validation_results"]:
                export_rows.append({
                    "image": item["image_name"],
                    "record_id": match_result.get("record_id"),
                    "matched_record": match_result.get("matched_brand"),
                    "match_confidence": match_result.get("confidence"),
                    "match_status": match_result.get("status"),
                    "overall_status": item["overall_status"],
                    "primary_issue": item["primary_issue"],
                    "field": result.get("field"),
                    "expected": result.get("expected"),
                    "detected": result.get("detected"),
                    "field_status": result.get("status"),
                    "match_type": result.get("match_type"),
                    "field_confidence": result.get("confidence"),
                    "explanation": result.get("explanation"),
                    "processing_time_seconds": item["processing_time"],
                    "match_notes": match_result.get("notes"),
                })
        else:
            export_rows.append({
                "image": item["image_name"],
                "record_id": match_result.get("record_id"),
                "matched_record": match_result.get("matched_brand"),
                "match_confidence": match_result.get("confidence"),
                "match_status": match_result.get("status"),
                "overall_status": item["overall_status"],
                "primary_issue": item["primary_issue"],
                "field": "",
                "expected": "",
                "detected": "",
                "field_status": "",
                "match_type": "",
                "field_confidence": "",
                "explanation": match_result.get("notes"),
                "processing_time_seconds": item["processing_time"],
                "match_notes": match_result.get("notes"),
            })

    return export_rows


def render_verification_results(summary_df, export_df, detailed_results, total_time):
    """
    Renders the most recent verification results from session_state.
    Keeping rendering separate from processing prevents download-button reruns
    from clearing the UI.
    """
    if summary_df is None or export_df is None or detailed_results is None:
        return

    st.subheader("Verification Results")
    st.markdown("### Batch Summary")

    total_labels = len(summary_df)
    pass_count = (summary_df["Overall Status"] == "Pass").sum()
    fail_count = (summary_df["Overall Status"] == "Fail").sum()
    review_count = (summary_df["Overall Status"] == "Needs Review").sum()
    error_count = (summary_df["Overall Status"] == "Error").sum()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Labels Processed", total_labels)
    col2.metric("Pass", int(pass_count))
    col3.metric("Fail", int(fail_count))
    col4.metric("Needs Review", int(review_count))
    col5.metric("Errors", int(error_count))

    st.dataframe(summary_df, use_container_width=True)

    if total_time is not None:
        st.info(f"Total batch processing time: {total_time} seconds")

    st.markdown("### Export Results")

    export_col1, export_col2 = st.columns(2)

    export_col1.download_button(
        label="Download Batch Summary CSV",
        data=summary_df.to_csv(index=False).encode("utf-8"),
        file_name="label_verification_batch_summary.csv",
        mime="text/csv",
    )

    export_col2.download_button(
        label="Download Detailed Validation CSV",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name="label_verification_detailed_results.csv",
        mime="text/csv",
    )

    st.markdown("### Detailed Results")

    for item in detailed_results:
        expander_title = (
            f'{item["image_name"]} | '
            f'{item["overall_status"]} | '
            f'{item["match_result"]["confidence"]}% | '
            f'{item["primary_issue"]}'
        )

        with st.expander(expander_title, expanded=False):
            match_result = item["match_result"]

            if item["overall_status"] == "Pass":
                st.success("PASS")
            elif item["overall_status"] == "Fail":
                st.error("FAIL")
            elif item["overall_status"] == "Error":
                st.error("ERROR")
            else:
                st.warning("NEEDS REVIEW")

            st.write(f"Primary Issue: {item['primary_issue']}")
            st.write(f"All Issues: {item['all_issues']}")

            col1, col2, col3, col4, col5 = st.columns(5)

            col1.metric("Matched Record", match_result["matched_brand"])
            col2.metric("Match Confidence", f'{match_result["confidence"]}%')
            col3.metric("Match Status", match_result["status"])
            col4.metric("Overall Status", item["overall_status"])
            col5.metric("Processing Time", f'{item["processing_time"]}s')

            st.write(f"Record ID: {match_result['record_id']}")
            st.write(f"Match Notes: {match_result['notes']}")

            if item["validation_results"]:
                st.markdown("#### Field Validation Results")

                results_df = pd.DataFrame(item["validation_results"])

                st.dataframe(
                    results_df[
                        [
                            "field",
                            "expected",
                            "detected",
                            "status",
                            "match_type",
                            "confidence",
                            "explanation",
                        ]
                    ],
                    use_container_width=True
                )

            with st.expander("View Raw OCR Text"):
                st.text(item["raw_text"])

            with st.expander("View Normalized Text"):
                st.text(item["normalized_text"])


st.set_page_config(
    page_title="Alcohol Label Verification App",
    page_icon="🏷️",
    layout="wide"
)

# ---------------------------------------------------
# SESSION STATE STORAGE
# ---------------------------------------------------
# Streamlit reruns the script when a download button is clicked.
# These keys preserve the most recent verification results so the
# page does not wipe the summary, exports, or detailed review panels.
if "summary_df" not in st.session_state:
    st.session_state.summary_df = None

if "export_df" not in st.session_state:
    st.session_state.export_df = None

if "detailed_results" not in st.session_state:
    st.session_state.detailed_results = None

if "total_time" not in st.session_state:
    st.session_state.total_time = None


st.title("Alcohol Label Verification App")
st.caption("Batch-first OCR-assisted label review prototype")

st.header("Step 1: Upload Application Records")
csv_file = st.file_uploader("Upload CSV file", type=["csv"])

records_df = None

if csv_file:
    records_df, missing_columns = load_csv(csv_file)

    if missing_columns:
        st.error(
            "The uploaded CSV is missing required fields: "
            + ", ".join(missing_columns)
        )
    else:
        st.success(f"CSV uploaded successfully. Records loaded: {len(records_df)}")
        st.dataframe(records_df, use_container_width=True)

st.header("Step 2: Upload Label Images")
image_files = st.file_uploader(
    "Upload PNG, JPG, or JPEG label images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if image_files:
    st.success(f"Images uploaded: {len(image_files)}")

st.header("Step 3: Verify Labels")

if st.button("Run Verification"):
    if csv_file is None:
        st.error("No CSV file was uploaded. Please upload an application records CSV first.")

    elif records_df is None:
        st.error("CSV could not be processed. Please fix the CSV file and try again.")

    elif not image_files:
        st.error("No image files were uploaded. Please upload at least one label image.")

    else:
        total_start = time.time()
        summary_rows = []
        detailed_results = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        total_images = len(image_files)

        for index, image_file in enumerate(image_files, start=1):
            start_time = time.time()
            status_text.info(
                f"Processing label {index} of {total_images}: {image_file.name}"
            )

            try:
                # Reset file pointer before OCR. This prevents weird behavior if Streamlit
                # has already touched the uploaded file object.
                image_file.seek(0)

                raw_text = extract_text_from_image(image_file)
                normalized_text = normalize_text(raw_text)

                match_result = find_best_record_match(
                    records_df,
                    normalized_text
                )

                matched_record = records_df[
                    records_df["record_id"] == match_result["record_id"]
                ]

                if matched_record.empty:
                    processing_time = round(time.time() - start_time, 2)
                    overall_status = "Needs Review"
                    validation_results = []
                    primary_issue = get_primary_issue(
                        overall_status,
                        match_result,
                        validation_results
                    )
                    all_issues = "No matching CSV record was available for validation."

                    summary_rows.append({
                        "Image": image_file.name,
                        "Matched Record": "No Match",
                        "Match Confidence": f'{match_result["confidence"]}%',
                        "Match Status": match_result["status"],
                        "Overall Status": overall_status,
                        "Primary Issue": primary_issue,
                        "All Issues": all_issues,
                        "Processing Time": f"{processing_time}s",
                    })

                    detailed_results.append({
                        "image_name": image_file.name,
                        "match_result": match_result,
                        "overall_status": overall_status,
                        "primary_issue": primary_issue,
                        "all_issues": all_issues,
                        "validation_results": validation_results,
                        "raw_text": raw_text,
                        "normalized_text": normalized_text,
                        "processing_time": processing_time,
                    })

                    status_text.info(
                        f"Completed label {index} of {total_images}: "
                        f"{image_file.name} — Elapsed: {processing_time} seconds"
                    )
                    progress_bar.progress(index / total_images)
                    continue

                matched_record = matched_record.iloc[0]

                overall_status, validation_results = validate_label(
                    matched_record,
                    normalized_text
                )

                # ---------------------------------------------------
                # SECOND-PASS RECORD CONFIRMATION
                # ---------------------------------------------------
                # If the initial OCR record match is below the Auto Match
                # threshold, but every required field validates against the
                # selected record, promote it to a reviewer-friendly confirmed
                # match. This keeps the human-in-the-loop logic while avoiding
                # unnecessary review flags when the required fields all pass.
                all_fields_passed = all(
                    result.get("status") == "Pass"
                    for result in validation_results
                )

                if all_fields_passed:
                    match_result["confidence"] = 100

                    if match_result.get("status") != "Auto Match":
                        match_result["status"] = "Confirmed Match"
                        match_result["notes"] = (
                            "Initial OCR record match confidence was below the "
                            "automatic match threshold, but all required fields "
                            "were successfully validated against the matched record."
                        )

                processing_time = round(time.time() - start_time, 2)
                primary_issue = get_primary_issue(
                    overall_status,
                    match_result,
                    validation_results
                )
                all_issues = build_field_issue_summary(validation_results)

                summary_rows.append({
                    "Image": image_file.name,
                    "Matched Record": match_result["matched_brand"],
                    "Match Confidence": f'{match_result["confidence"]}%',
                    "Match Status": match_result["status"],
                    "Overall Status": overall_status,
                    "Primary Issue": primary_issue,
                    "All Issues": all_issues,
                    "Processing Time": f"{processing_time}s",
                })

                detailed_results.append({
                    "image_name": image_file.name,
                    "match_result": match_result,
                    "overall_status": overall_status,
                    "primary_issue": primary_issue,
                    "all_issues": all_issues,
                    "validation_results": validation_results,
                    "raw_text": raw_text,
                    "normalized_text": normalized_text,
                    "processing_time": processing_time,
                })

                status_text.info(
                    f"Completed label {index} of {total_images}: "
                    f"{image_file.name} — Elapsed: {processing_time} seconds"
                )

            except Exception as error:
                processing_time = round(time.time() - start_time, 2)
                overall_status = "Error"

                match_result = {
                    "record_id": None,
                    "matched_brand": "Error",
                    "confidence": 0,
                    "status": "Error",
                    "notes": str(error),
                }

                primary_issue = get_primary_issue(
                    overall_status,
                    match_result,
                    []
                )
                all_issues = str(error)

                summary_rows.append({
                    "Image": image_file.name,
                    "Matched Record": "Error",
                    "Match Confidence": "0%",
                    "Match Status": "Error",
                    "Overall Status": overall_status,
                    "Primary Issue": primary_issue,
                    "All Issues": all_issues,
                    "Processing Time": f"{processing_time}s",
                })

                detailed_results.append({
                    "image_name": image_file.name,
                    "match_result": match_result,
                    "overall_status": overall_status,
                    "primary_issue": primary_issue,
                    "all_issues": all_issues,
                    "validation_results": [],
                    "raw_text": "",
                    "normalized_text": "",
                    "processing_time": processing_time,
                })

                status_text.error(
                    f"Completed label {index} of {total_images}: "
                    f"{image_file.name} — Error after {processing_time} seconds"
                )

            progress_bar.progress(index / total_images)

        total_time = round(time.time() - total_start, 2)
        status_text.success(f"Finished processing {total_images} label(s).")

        summary_df = pd.DataFrame(summary_rows)
        export_df = pd.DataFrame(build_export_rows(detailed_results))

        # Persist results so Streamlit reruns from download buttons do not wipe the page.
        st.session_state.summary_df = summary_df
        st.session_state.export_df = export_df
        st.session_state.detailed_results = detailed_results
        st.session_state.total_time = total_time

# Always render from session_state after processing. This is what keeps results
# visible after Streamlit reruns caused by download button clicks.
render_verification_results(
    st.session_state.summary_df,
    st.session_state.export_df,
    st.session_state.detailed_results,
    st.session_state.total_time,
)
