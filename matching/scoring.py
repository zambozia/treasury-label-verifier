from rapidfuzz import fuzz


def score_field(expected_value: str, ocr_text: str) -> int:
    """
    Scores how well an expected field value appears in OCR text.

    Returns a score from 0 to 100.
    """
    if not expected_value:
        return 0

    expected = str(expected_value).lower().strip()
    text = str(ocr_text).lower().strip()

    if not expected or not text:
        return 0

    if expected in text:
        return 100

    return fuzz.partial_ratio(expected, text)


def calculate_record_score(record, ocr_text: str) -> int:
    """
    Calculates a weighted match score for one CSV record.
    """
    brand_score = score_field(record.get("brand_name", ""), ocr_text)
    class_score = score_field(record.get("class_type", ""), ocr_text)
    alcohol_score = score_field(record.get("alcohol_content", ""), ocr_text)
    net_score = score_field(record.get("net_contents", ""), ocr_text)

    weighted_score = (
        brand_score * 0.45
        + class_score * 0.25
        + alcohol_score * 0.20
        + net_score * 0.10
    )

    return round(weighted_score)


def get_match_status(score: int) -> str:
    """
    Converts numeric score into matching status.
    """
    if score >= 95:
        return "Auto Match"

    if score >= 70:
        return "Needs Review"

    return "No Match"