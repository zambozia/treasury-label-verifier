import re


def extract_alcohol_content(text: str) -> str:
    if not text:
        return ""

    patterns = [
        r"\b\d{1,3}\s?%\s?alc\.?\s*/?\s?vol\.?\b",
        r"\b\d{1,3}\s?%\s?alcohol\s?by\s?volume\b",
        r"\b\d{1,3}\s?%\s?abv\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0)

    return ""


def extract_net_contents(text: str) -> str:
    if not text:
        return ""

    patterns = [
        r"\b\d{2,4}\s?m\s?l\b",
        r"\b\d{2,4}\s?ml\b",
        r"\b\d{2,4}\s?milliliters?\b",
        r"\b\d+\s?fl\.?\s?oz\.?\b",
        r"\b\d+\s?floz\b",
        r"\b\d+\s?oz\.?\b",
        r"\b\d+\s?pint\b",
        r"\b\d+\s?pt\.?\b",
        r"\b1\s?pint\b",
        r"\b1\s?pt\.?\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0)

    return ""


def contains_expected_text(expected: str, ocr_text: str) -> bool:
    if not expected or not ocr_text:
        return False

    expected_clean = re.sub(r"\s+", " ", expected.lower().strip())
    ocr_clean = re.sub(r"\s+", " ", ocr_text.lower().strip())

    return expected_clean in ocr_clean