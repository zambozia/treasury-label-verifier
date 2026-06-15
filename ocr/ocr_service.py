from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
import time


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

MAX_SECONDS = 5.0
MAX_IMAGE_WIDTH = 1800


def pil_to_cv(image):
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def limit_image_size(image):
    width, height = image.size

    if width <= MAX_IMAGE_WIDTH:
        return image

    scale = MAX_IMAGE_WIDTH / width
    new_height = int(height * scale)

    return image.resize((MAX_IMAGE_WIDTH, new_height), Image.LANCZOS)


def resize_image(image, scale=2):
    return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)


def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def sharpen_image(gray):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(gray, -1, kernel)


def threshold_image(gray):
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )


def otsu_threshold(gray):
    _, processed = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return processed


def run_tesseract(image, psm=11):
    config = f"--oem 3 --psm {psm}"
    return pytesseract.image_to_string(image, config=config)


def clean_ocr_line(line):
    line = line.strip()
    line = re.sub(r"\s+", " ", line)
    return line


def merge_ocr_outputs(text_outputs):
    seen = set()
    merged_lines = []

    for text in text_outputs:
        if not text:
            continue

        for line in text.splitlines():
            cleaned = clean_ocr_line(line)

            if len(cleaned) < 2:
                continue

            key = cleaned.lower()

            if key not in seen:
                seen.add(key)
                merged_lines.append(cleaned)

    return "\n".join(merged_lines)


def score_ocr_text(text):
    if not text:
        return 0

    text_lower = text.lower()
    score = 0

    useful_patterns = [
        r"government\s+warning",
        r"surgeon\s+general",
        r"pregnancy",
        r"birth\s+defects",
        r"\d{1,3}\s*%\s*alc",
        r"\d+\s*ml",
        r"\d+\s*fl\.?\s*oz",
        r"whiskey|whisky|bourbon|tequila|rum|beer|ale|wine|liqueur|pilsner",
        r"bottled|produced|distilled|brewed|imported",
    ]

    for pattern in useful_patterns:
        if re.search(pattern, text_lower):
            score += 25

    score += min(len(text_lower), 1200) * 0.02

    garbage_count = len(re.findall(r"[^a-zA-Z0-9\s%./,&:;()'-]", text))
    score -= garbage_count * 0.15

    return score


def has_core_label_signals(text):
    text_lower = text.lower()

    has_alcohol = bool(re.search(r"\d{1,3}\s*%\s*alc", text_lower))
    has_net = bool(re.search(r"\d+\s*(ml|fl\.?\s*oz|oz|pint|pt)", text_lower))
    has_warning = bool(re.search(r"government\s+warning", text_lower))
    has_type = bool(re.search(
        r"whiskey|whisky|bourbon|tequila|rum|beer|ale|wine|liqueur|pilsner",
        text_lower
    ))

    return has_alcohol and has_net and has_warning and has_type


def extract_text_from_image(uploaded_image) -> str:
    start_time = time.time()

    image = Image.open(uploaded_image).convert("RGB")
    image = limit_image_size(image)

    cv_image = pil_to_cv(image)

    gray_1x = grayscale(cv_image)
    gray_2x = resize_image(gray_1x, 2)

    sharp_2x = sharpen_image(gray_2x)
    threshold_2x = threshold_image(gray_2x)
    otsu_2x = otsu_threshold(gray_2x)

    inverted_gray_2x = cv2.bitwise_not(gray_2x)
    inverted_threshold_2x = cv2.bitwise_not(threshold_2x)
    inverted_otsu_2x = cv2.bitwise_not(otsu_2x)

    candidates = [
        ("gray_2x_psm11", gray_2x, 11),
        ("gray_2x_psm6", gray_2x, 6),
        ("sharp_2x_psm11", sharp_2x, 11),
        ("sharp_2x_psm6", sharp_2x, 6),
        ("threshold_2x_psm11", threshold_2x, 11),
        ("threshold_2x_psm6", threshold_2x, 6),
        ("otsu_2x_psm11", otsu_2x, 11),
        ("otsu_2x_psm6", otsu_2x, 6),
        ("inverted_gray_2x_psm11", inverted_gray_2x, 11),
        ("inverted_threshold_2x_psm11", inverted_threshold_2x, 11),
        ("inverted_otsu_2x_psm11", inverted_otsu_2x, 11),
    ]

    text_outputs = []
    best_text = ""
    best_score = -1

    for name, candidate_image, psm in candidates:
        elapsed = time.time() - start_time

        if elapsed >= MAX_SECONDS:
            break

        text = run_tesseract(candidate_image, psm)

        if text and len(text.strip()) > 10:
            text_outputs.append(text)

            combined_text = merge_ocr_outputs(text_outputs)
            combined_score = score_ocr_text(combined_text)

            if combined_score > best_score:
                best_score = combined_score
                best_text = combined_text

            if has_core_label_signals(combined_text):
                return combined_text

    return best_text if best_text else merge_ocr_outputs(text_outputs)