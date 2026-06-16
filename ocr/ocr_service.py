from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
import time
import os

if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

# Hard OCR budget. The app's target is under 5 seconds per label, so this
# service stops OCR work before the overall app processing reaches that limit.
MAX_SECONDS = 7.75
MAX_IMAGE_WIDTH = 1600
MIN_PASS_TIMEOUT = 0.35
MAX_PASS_TIMEOUT = 1.25


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


def run_tesseract(image, psm=11, timeout=0.85):
    """
    Runs one Tesseract pass with a real subprocess timeout.

    The earlier version checked the 5-second budget only between passes.
    If one Tesseract call took 30 seconds, the app could not stop it.
    This timeout prevents a single OCR pass from taking over the whole label.
    """
    config = f"--oem 3 --psm {psm}"

    try:
        return pytesseract.image_to_string(
            image,
            config=config,
            timeout=timeout
        )
    except RuntimeError:
        # pytesseract raises RuntimeError when the timeout is exceeded.
        # Treat that pass as no useful text and continue while budget remains.
        return ""


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


def detected_core_fields(text):
    """
    Tracks OCR progress across passes.

    Important limitation: this OCR layer does not know the matched CSV record yet,
    so it cannot validate exact Brand Name or Class/Type values here. It can only
    detect whether core label signals are present. Actual field validation still
    happens later in validation/validator.py.
    """
    text_lower = text.lower() if text else ""

    return {
        "alcohol_content": bool(re.search(r"\d{1,3}\s*%\s*(alc|abv|alcohol)", text_lower)),
        "net_contents": bool(re.search(r"\d+\s*(ml|m\s*l|fl\.?\s*oz|oz|pint|pt)", text_lower)),
        "government_warning": bool(re.search(r"government\s+warning", text_lower)),
        "class_type_signal": bool(re.search(
            r"whiskey|whisky|bourbon|tequila|rum|beer|ale|wine|liqueur|pilsner",
            text_lower
        )),
    }


def has_core_label_signals(text):
    fields = detected_core_fields(text)
    return all(fields.values())


def remaining_field_names(text):
    fields = detected_core_fields(text)
    return [name for name, found in fields.items() if not found]


def extract_text_from_image(uploaded_image) -> str:
    start_time = time.time()

    image = Image.open(uploaded_image).convert("RGB")
    image = limit_image_size(image)

    cv_image = pil_to_cv(image)

    gray_1x = grayscale(cv_image)
    gray_2x = resize_image(gray_1x, 2)

    # Build cheaper/high-yield candidates first. More expensive preprocessing is
    # only generated if the time budget allows continued OCR attempts.
    candidates = [
        ("gray_1x_psm6", lambda: gray_1x, 6),
        ("gray_1x_psm11", lambda: gray_1x, 11),
        ("gray_2x_psm6", lambda: gray_2x, 6),
        ("gray_2x_psm11", lambda: gray_2x, 11),
        ("sharp_2x_psm6", lambda: sharpen_image(gray_2x), 6),
        ("threshold_2x_psm6", lambda: threshold_image(gray_2x), 6),
        ("otsu_2x_psm6", lambda: otsu_threshold(gray_2x), 6),
        ("inverted_threshold_2x_psm11", lambda: cv2.bitwise_not(threshold_image(gray_2x)), 11),
    ]

    text_outputs = []
    best_text = ""
    best_score = -1

    for name, image_factory, psm in candidates:
        elapsed = time.time() - start_time
        remaining = MAX_SECONDS - elapsed

        if remaining <= MIN_PASS_TIMEOUT:
            break

        candidate_image = image_factory()
        pass_timeout = max(
            MIN_PASS_TIMEOUT,
            min(MAX_PASS_TIMEOUT, remaining - 0.05)
        )

        text = run_tesseract(candidate_image, psm, timeout=pass_timeout)

        if text and len(text.strip()) > 10:
            text_outputs.append(text)

            combined_text = merge_ocr_outputs(text_outputs)
            combined_score = score_ocr_text(combined_text)

            if combined_score > best_score:
                best_score = combined_score
                best_text = combined_text

            # Stop early when the merged OCR output contains the core label
            # signals needed for downstream matching and validation.
            if has_core_label_signals(combined_text):
                return combined_text

    return best_text if best_text else merge_ocr_outputs(text_outputs)
