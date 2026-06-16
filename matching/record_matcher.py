import pandas as pd

from matching.scoring import calculate_record_score, get_match_status


def is_blank_value(value) -> bool:
    """
    Returns True when a CSV value is empty, NaN, or whitespace only.
    """
    if pd.isna(value):
        return True

    return str(value).strip() == ""


def find_best_record_match(records_df, ocr_text: str) -> dict:
    """
    Finds the best matching CSV record for the OCR text.

    Returns:
    {
        "record_id": "...",
        "matched_brand": "...",
        "confidence": 97,
        "status": "Auto Match",
        "notes": "..."
    }
    """
    if records_df is None or records_df.empty:
        return {
            "record_id": None,
            "matched_brand": "No records available",
            "confidence": 0,
            "status": "No Match",
            "notes": "No CSV records were available for matching."
        }

    best_record = None
    best_score = -1

    for _, record in records_df.iterrows():
        brand_name = record.get("brand_name", "")

        if is_blank_value(brand_name):
            continue

        score = calculate_record_score(record, ocr_text)

        if score > best_score:
            best_score = score
            best_record = record

    if best_record is None:
        return {
            "record_id": None,
            "matched_brand": "No Match",
            "confidence": 0,
            "status": "No Match",
            "notes": "No valid CSV records were available for matching."
        }

    status = get_match_status(best_score)

    if status == "No Match":
        return {
            "record_id": None,
            "matched_brand": "No Match",
            "confidence": best_score,
            "status": "No Match",
            "notes": "No confident record match found. Manual review required."
        }

    if status == "Auto Match":
        notes = "High-confidence match found."
    elif status == "Needs Review":
        notes = "Possible match found. Human review recommended."
    else:
        notes = "No confident record match found. Manual review required."

    return {
        "record_id": best_record.get("record_id", None),
        "matched_brand": best_record.get("brand_name", "Unknown"),
        "confidence": best_score,
        "status": status,
        "notes": notes
    }