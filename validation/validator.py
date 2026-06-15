from rapidfuzz import fuzz

from validation.field_extractor import (
    extract_alcohol_content,
    extract_net_contents,
    contains_expected_text,
)

from validation.warning_rules import detect_government_warning


def build_result(field, expected, detected, status, match_type, confidence, explanation):
    return {
        "field": field,
        "expected": expected,
        "detected": detected,
        "status": status,
        "match_type": match_type,
        "confidence": confidence,
        "explanation": explanation,
    }


def normalize_exact_value(value):
    if not value:
        return ""

    value = str(value).lower()
    value = value.replace(" ", "")
    value = value.replace(".", "")
    value = value.replace("/", "")
    value = value.replace("-", "")
    value = value.replace("|", "")
    value = value.replace(",", "")

    value = value.replace("milliliters", "ml")
    value = value.replace("milliliter", "ml")
    value = value.replace("fluidounces", "floz")
    value = value.replace("flounces", "floz")
    value = value.replace("floz", "floz")

    return value.strip()


def validate_fuzzy_field(field_name, expected, ocr_text):
    if not expected:
        return build_result(
            field_name,
            expected,
            "",
            "Missing",
            "Fuzzy",
            0,
            f"No expected value was provided for {field_name}.",
        )

    if contains_expected_text(expected, ocr_text):
        return build_result(
            field_name,
            expected,
            expected,
            "Pass",
            "Exact Text Found",
            100,
            f"{field_name} was found directly in the OCR text.",
        )

    expected_text = str(expected).lower()
    ocr_text_lower = str(ocr_text).lower()

    partial_score = fuzz.partial_ratio(expected_text, ocr_text_lower)
    token_set_score = fuzz.token_set_ratio(expected_text, ocr_text_lower)
    token_sort_score = fuzz.token_sort_ratio(expected_text, ocr_text_lower)

    score = max(partial_score, token_set_score, token_sort_score)

    if score >= 85:
        status = "Pass"
        explanation = f"{field_name} matches after fuzzy/token comparison."
    elif score >= 65:
        status = "Needs Review"
        explanation = f"{field_name} may match, but confidence is not high enough."
    else:
        status = "Missing"
        explanation = f"{field_name} was not confidently found in the OCR text."

    return build_result(
        field_name,
        expected,
        expected if score >= 65 else "",
        status,
        "Fuzzy Token Match",
        round(score),
        explanation,
    )


def validate_exact_field(field_name, expected, detected):
    if not expected:
        return build_result(
            field_name,
            expected,
            detected,
            "Missing",
            "Normalized Exact",
            0,
            f"No expected value was provided for {field_name}.",
        )

    if not detected:
        return build_result(
            field_name,
            expected,
            "",
            "Missing",
            "Normalized Exact",
            0,
            f"{field_name} was not found in the OCR text.",
        )

    expected_clean = normalize_exact_value(expected)
    detected_clean = normalize_exact_value(detected)

    if expected_clean == detected_clean:
        return build_result(
            field_name,
            expected,
            detected,
            "Pass",
            "Normalized Exact",
            100,
            f"{field_name} matches the expected value after normalization.",
        )

    return build_result(
        field_name,
        expected,
        detected,
        "Fail",
        "Normalized Exact",
        0,
        f"{field_name} does not match the expected value after normalization.",
    )


def validate_government_warning(expected, ocr_text):
    detected = detect_government_warning(ocr_text)

    if not detected:
        return build_result(
            "Government Warning",
            expected,
            "",
            "Missing",
            "Strict",
            0,
            "Government warning was not found in the OCR text.",
        )

    return build_result(
        "Government Warning",
        expected,
        detected,
        "Pass",
        "Strict",
        100,
        "Government warning heading was found.",
    )


def determine_overall_status(results):
    statuses = [result["status"] for result in results]

    if "Fail" in statuses:
        return "Fail"

    if "Missing" in statuses or "Needs Review" in statuses:
        return "Needs Review"

    return "Pass"


def validate_label(record, ocr_text):
    alcohol_detected = extract_alcohol_content(ocr_text)
    net_detected = extract_net_contents(ocr_text)

    results = [
        validate_fuzzy_field("Brand Name", record.get("brand_name", ""), ocr_text),
        validate_fuzzy_field("Class / Type", record.get("class_type", ""), ocr_text),
        validate_exact_field("Alcohol Content", record.get("alcohol_content", ""), alcohol_detected),
        validate_exact_field("Net Contents", record.get("net_contents", ""), net_detected),
        validate_government_warning(record.get("government_warning", ""), ocr_text),
    ]

    overall_status = determine_overall_status(results)

    return overall_status, results