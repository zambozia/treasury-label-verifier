import re


def detect_government_warning(ocr_text: str) -> str:
    if not ocr_text:
        return ""

    text = ocr_text.lower()

    pattern = r"government\s+warning\s*:?"

    if re.search(pattern, text):
        return "GOVERNMENT WARNING:"

    return ""