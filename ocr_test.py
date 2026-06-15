from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

img = Image.open(r"sample-labels\test\test_label4.png")

text = pytesseract.image_to_string(img)

print(text)


