import sys
import os
import io
import pytest
from PIL import Image, ImageDraw

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ocr import perform_ocr, parse_document_fields, _repair_aadhaar_ocr, _repair_pan_ocr, _parse_dob


def create_sample_aadhaar() -> bytes:
    img = Image.new('RGB', (800, 500), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 30), "GOVERNMENT OF INDIA", fill=(0, 0, 0))
    draw.text((40, 60), "Unique Identification Authority of India", fill=(40, 40, 40))
    draw.text((40, 150), "RAJESH KUMAR SHARMA", fill=(0, 0, 0))
    draw.text((40, 200), "DOB: 14/08/1988", fill=(0, 0, 0))
    draw.text((40, 250), "MALE", fill=(0, 0, 0))
    draw.text((40, 350), "5489 2104 9811", fill=(0, 0, 0))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def create_sample_pan() -> bytes:
    img = Image.new('RGB', (800, 500), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 30), "INCOME TAX DEPARTMENT", fill=(0, 0, 0))
    draw.text((40, 60), "GOVT. OF INDIA", fill=(40, 40, 40))
    draw.text((40, 130), "Permanent Account Number Card", fill=(0, 0, 0))
    draw.text((40, 180), "NAME", fill=(80, 80, 80))
    draw.text((40, 210), "PRIYA SHARMA", fill=(0, 0, 0))
    draw.text((40, 260), "FATHER'S NAME", fill=(80, 80, 80))
    draw.text((40, 290), "RAMESH SHARMA", fill=(0, 0, 0))
    draw.text((40, 340), "DOB: 22/05/1992", fill=(0, 0, 0))
    draw.text((40, 400), "BKZPS8491K", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def create_sample_passport() -> bytes:
    img = Image.new('RGB', (900, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 30), "REPUBLIC OF INDIA / PASSPORT", fill=(0, 0, 0))
    draw.text((40, 80), "PASSPORT NO: Z1234567", fill=(0, 0, 0))
    draw.text((40, 130), "SURNAME", fill=(80, 80, 80))
    draw.text((40, 160), "VERMA", fill=(0, 0, 0))
    draw.text((40, 210), "GIVEN NAMES", fill=(80, 80, 80))
    draw.text((40, 240), "ANANYA", fill=(0, 0, 0))
    draw.text((40, 290), "NATIONALITY: INDIAN", fill=(0, 0, 0))
    draw.text((40, 340), "SEX: F", fill=(0, 0, 0))
    draw.text((40, 390), "DATE OF BIRTH: 10/11/1995", fill=(0, 0, 0))
    draw.text((40, 440), "DATE OF EXPIRY: 09/11/2035", fill=(0, 0, 0))
    draw.text((40, 500), "P<INDVERMA<<ANANYA<<<<<<<<<<<<<<<<<<<<<<<<<<", fill=(0, 0, 0))
    draw.text((40, 540), "Z1234567<8IND9511105F3511093<<<<<<<<<<<<<<0", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def test_aadhaar_ocr_detection():
    aadhaar_bytes = create_sample_aadhaar()
    ocr_res = perform_ocr(aadhaar_bytes)
    assert ocr_res["engine_used"] == "tesseract"
    assert len(ocr_res["raw_text"]) > 0

    fields = parse_document_fields(ocr_res)
    assert fields["doc_type"] == "AADHAAR"
    assert fields["id_number"] == "5489 2104 9811"
    assert fields["gender"] == "MALE"
    assert fields["dob"] == "14/08/1988"
    assert "Rajesh" in (fields["name"] or "")


def test_pan_ocr_detection():
    pan_bytes = create_sample_pan()
    ocr_res = perform_ocr(pan_bytes)
    assert ocr_res["engine_used"] == "tesseract"

    fields = parse_document_fields(ocr_res)
    assert fields["doc_type"] == "PAN"
    assert fields["id_number"] == "BKZPS8491K"
    assert fields["dob"] == "22/05/1992"
    assert "PRIYA" in (fields["name"] or "")


def test_passport_ocr_detection():
    pp_bytes = create_sample_passport()
    ocr_res = perform_ocr(pp_bytes)
    assert ocr_res["engine_used"] == "tesseract"

    fields = parse_document_fields(ocr_res)
    assert fields["doc_type"] == "PASSPORT"
    assert fields["id_number"] == "Z1234567"
    assert fields["nationality"] == "INDIAN"
    assert fields["gender"] == "FEMALE"


def test_ocr_repair_helpers():
    # Aadhaar repair: O replaced by 0 in valid Verhoeff Aadhaar 548921049811
    repaired_aadhaar = _repair_aadhaar_ocr("Aadhaar: 5489 21O4 9811")
    assert repaired_aadhaar == "5489 2104 9811"

    # PAN repair: 0 instead of O or 1 instead of I in BKZPS8491K
    repaired_pan = _repair_pan_ocr("Account: BKZPS8491K")
    assert repaired_pan == "BKZPS8491K"

    # Date parsing
    dob, _ = _parse_dob("Date of birth 14/08/1988 on record")
    assert dob == "14/08/1988"

    dob_text, _ = _parse_dob("DOB: 14 Aug 1988")
    assert dob_text == "14/08/1988"


if __name__ == "__main__":
    print("[*] Running OCR detection test suite...")
    test_aadhaar_ocr_detection()
    print(" [+] Aadhaar OCR detection: PASS")
    test_pan_ocr_detection()
    print(" [+] PAN OCR detection: PASS")
    test_passport_ocr_detection()
    print(" [+] Passport OCR detection: PASS")
    test_ocr_repair_helpers()
    print(" [+] OCR repair helpers: PASS")
    print("\n[ALL OCR DETECTION TESTS PASSED SUCCESSFULLY!]")
