import re


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    text = text.replace("\n", " ")

    text = re.sub(r"\s+", " ", text)

    # Normalize common OCR variations

    text = text.replace("750ml", "750 ml")
    text = text.replace("375ml", "375 ml")
    text = text.replace("1l", "1 l")

    text = text.replace("alc. / vol.", "alc./vol.")
    text = text.replace("alc./vol", "alc./vol.")
    text = text.replace("alc / vol", "alc./vol.")
    text = text.replace("alc/vol", "alc./vol.")

    text = text.replace("governmentwarning", "government warning")
    text = text.replace("govemment warning", "government warning")

    return text.strip()