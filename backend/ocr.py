"""
OCR & Information Extraction Module for Identity Documents
Supports fast multi-pass OCR via OpenCV and Pytesseract / EasyOCR.
Extracts Aadhaar, PAN, and Indian Passport with high precision and watermark filtering.
"""

import io
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# Try importing cv2, pytesseract, easyocr
try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import easyocr
    _easyocr_reader = None
except ImportError:
    easyocr = None
    _easyocr_reader = None


def get_easyocr_reader():
    global _easyocr_reader
    if easyocr is not None and _easyocr_reader is None:
        try:
            _easyocr_reader = easyocr.Reader(['en', 'hi'], gpu=False)
        except Exception as e:
            logger.warning(f"EasyOCR reader init failed: {e}")
    return _easyocr_reader


def preprocess_image(image_bytes: bytes) -> List[Tuple[str, Image.Image]]:
    """
    Applies optimized, high-performance image enhancement pipelines.
    Returns 3 key representations to maximize accuracy without latency overhead.
    """
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    results: List[Tuple[str, Image.Image]] = [("raw", pil_image)]

    if cv2 is None:
        return results

    open_cv_image = np.array(pil_image)
    open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

    # 1. Resize if image is small
    h, w = open_cv_image.shape[:2]
    if w < 1200:
        scale_factor = 1200 / w
        open_cv_image = cv2.resize(
            open_cv_image,
            (int(w * scale_factor), int(h * scale_factor)),
            interpolation=cv2.INTER_CUBIC
        )

    # 2. Grayscale & CLAHE (Contrast-Limited Adaptive Histogram Equalization)
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    clahe_img = clahe.apply(gray)
    results.append(("clahe", Image.fromarray(clahe_img)))

    # 3. Adaptive Threshold (for crisp text contours)
    thresh = cv2.adaptiveThreshold(
        clahe_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
    )
    results.append(("threshold", Image.fromarray(thresh)))

    return results


def perform_ocr(image_bytes: bytes) -> Dict[str, Any]:
    """
    Executes fast, targeted multi-pass OCR on document image.
    Uses PSM 6 (uniform block) and PSM 3 (auto page segmentation).
    """
    preprocessed_images = preprocess_image(image_bytes)
    raw_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    best_text = ""
    all_texts: List[str] = []
    ocr_data = []
    engine_used = "none"

    if pytesseract is not None:
        try:
            # Pass 1: CLAHE image with PSM 6 (best for identity card layouts)
            clahe_img = next((img for label, img in preprocessed_images if label == "clahe"), raw_pil)
            txt1 = pytesseract.image_to_string(clahe_img, lang='eng', config='--psm 6').strip()
            if txt1:
                all_texts.append(txt1)
                best_text = txt1
                engine_used = "tesseract"

            # Pass 2: Raw / Grayscale image with PSM 3 (auto segmentation)
            txt2 = pytesseract.image_to_string(raw_pil, lang='eng', config='--psm 3').strip()
            if txt2:
                all_texts.append(txt2)
                if len(txt2) > len(best_text):
                    best_text = txt2
                    engine_used = "tesseract"

            # Pass 3: Thresholded image with PSM 6 (great for MRZ / stamped text)
            thresh_img = next((img for label, img in preprocessed_images if label == "threshold"), None)
            if thresh_img:
                txt3 = pytesseract.image_to_string(thresh_img, lang='eng', config='--psm 6').strip()
                if txt3:
                    all_texts.append(txt3)
                    if len(txt3) > len(best_text):
                        best_text = txt3

            # Extract word bounding boxes and confidences from CLAHE image
            try:
                data_dict = pytesseract.image_to_data(clahe_img, output_type=pytesseract.Output.DICT)
                for i in range(len(data_dict['text'])):
                    t = data_dict['text'][i].strip()
                    conf = int(data_dict['conf'][i])
                    if t and conf > 15:
                        ocr_data.append({
                            "text": t,
                            "conf": conf,
                            "left": data_dict['left'][i],
                            "top": data_dict['top'][i],
                            "width": data_dict['width'][i],
                            "height": data_dict['height'][i]
                        })
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Pytesseract failed: {e}")

    # Fallback to EasyOCR if tesseract yielded nothing
    if not best_text.strip():
        reader = get_easyocr_reader()
        if reader:
            try:
                open_cv_raw = np.array(raw_pil)
                results = reader.readtext(open_cv_raw)
                lines = [res[1] for res in results if res[1].strip()]
                best_text = "\n".join(lines)
                all_texts.append(best_text)
                engine_used = "easyocr"
                for res in results:
                    ocr_data.append({
                        "text": res[1],
                        "conf": int(res[2] * 100),
                        "box": res[0]
                    })
            except Exception as e:
                logger.warning(f"EasyOCR failed: {e}")

    ocr_lines = [line.strip() for line in best_text.split('\n') if line.strip()]

    return {
        "raw_text": best_text,
        "all_texts": all_texts,
        "lines": ocr_lines,
        "ocr_data": ocr_data,
        "engine_used": engine_used
    }


# ==============================================================================
# WATERMARK & NOISE FILTERING
# ==============================================================================

_NOISE_KEYWORDS = frozenset([
    # Government & Structural Headers
    "GOVERNMENT", "INDIA", "AUTHORITY", "AADHAAR", "UIDAI", "ISSUE",
    "UNIQUE", "IDENTIFICATION", "PRINT", "ADDRESS", "MERA", "PEHCHAN",
    "ENROLMENT", "ENROLLMENT", "INCOME", "TAX", "PERMANENT", "ACCOUNT",
    "DEPARTMENT", "BHARAT", "SARKAR", "VID", "VALID", "DOWNLOAD",
    "GENERATED", "LETTER", "DATE", "HELP", "WWW", "HTTP", "COM",
    "MALE", "FEMALE", "DOB", "YEAR", "BIRTH", "SIGNATURE", "HOLDER",
    # Passport Specific Terms
    "PASSPORT", "REPUBLIC", "NATIONALITY", "INDIAN", "HYDERABAD",
    "SURNAME", "GIVEN", "NAME", "NAMES", "SEX", "CODE", "TYPE",
    "COUNTRY", "PASSEPORT", "MINISTRY", "EXTERNAL", "AFFAIRS",
    "REGIONAL", "OFFICE", "OFFICER", "ASSISTANT", "FILE", "NO",
    # Watermarks & Stock Sample Sites
    "SAMPLE", "SPECIMEN", "WATERMARK", "IMMIHELP", "IMMIHELP.COM",
    "SHUTTERSTOCK", "GETTY", "ALAMY", "DEPOSITPHOTOS", "DREAMSTIME",
    "STOCK", "PHOTO", "PREVIEW", "DEMO", "ILLUSTRATION", "VECTOR"
])


def _is_header_or_noise(text: str) -> bool:
    """Checks if a string is header text, watermark noise, domain name, or non-name."""
    upper = text.upper().strip()
    if not upper or len(upper) < 3:
        return True

    # Reject web domains, URLs, email addresses
    if re.search(r'\.(COM|ORG|NET|IN|GOV|EDU|IO|CO|XYZ)\b', upper) or "HTTP" in upper or "WWW." in upper:
        return True

    # Reject obvious watermark tokens
    if any(wm in upper for wm in ["SAMPLE", "IMMIHELP", "SPECIMEN", "WATERMARK", "STOCK"]):
        return True

    words = [w.strip('.,:-/()[]{}') for w in upper.split() if w.strip('.,:-/()[]{}')]
    if not words:
        return True

    noise_count = sum(1 for w in words if w in _NOISE_KEYWORDS)
    if noise_count / len(words) >= 0.4:
        return True

    # Reject lines that are mostly numeric
    digit_count = sum(1 for ch in text if ch.isdigit())
    if digit_count / len(text) > 0.35:
        return True

    return False


def _clean_name_candidate(text: str) -> str:
    """Cleans a raw OCR line into a proper name string."""
    cleaned = re.sub(r'[^A-Za-z\s\.]', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    words = cleaned.split()
    filtered = []
    for i, w in enumerate(words):
        w_clean = w.strip('. ')
        if len(w_clean) >= 2:
            if w_clean.upper() not in _NOISE_KEYWORDS:
                filtered.append(w_clean.capitalize())
        elif i == len(words) - 1 and len(w_clean) == 1 and w.endswith('.'):
            filtered.append(w)
    return " ".join(filtered).strip(" .-_:,;/\\'\"")


def _score_name_candidate(name: str) -> int:
    """Scores candidate name plausibility."""
    if not name or len(name) < 3 or _is_header_or_noise(name):
        return 0
    words = name.split()
    score = 0
    if 2 <= len(words) <= 4:
        score += 35
    elif len(words) == 1 and len(name) >= 4:
        score += 15
    avg_len = sum(len(w) for w in words) / len(words) if words else 0
    if avg_len >= 3.5:
        score += 25
    if not any(ch.isdigit() for ch in name):
        score += 20
    if 5 <= len(name) <= 35:
        score += 20
    return score


def _extract_best_name(lines: List[str], dob_line_idx: int, all_texts: List[str]) -> Tuple[Optional[str], int]:
    """Extracts best demographic name from OCR lines."""
    candidates: List[Tuple[str, int]] = []

    # 1. Line immediately before DOB (strong Aadhaar signal)
    if dob_line_idx > 0:
        for offset in [1, 2]:
            idx = dob_line_idx - offset
            if 0 <= idx < len(lines):
                raw_line = lines[idx]
                if not _is_header_or_noise(raw_line):
                    name = _clean_name_candidate(raw_line)
                    s = _score_name_candidate(name)
                    if s > 0:
                        candidates.append((name, s + 30))

    # 2. Lines following explicit Name / Given Name labels
    for i, line in enumerate(lines):
        upper = line.upper().strip()
        if re.search(r'\b(GIVEN\s*NAME|GIVEN\s*NAMES|NAME|FULL\s*NAME)\b', upper):
            if i + 1 < len(lines):
                raw = lines[i + 1]
                if not _is_header_or_noise(raw):
                    name = _clean_name_candidate(raw)
                    s = _score_name_candidate(name)
                    if s > 0:
                        candidates.append((name, s + 35))

    # 3. Consensus across all OCR passes
    for txt in all_texts:
        for l in txt.split('\n'):
            l_clean = l.strip()
            if not _is_header_or_noise(l_clean):
                name = _clean_name_candidate(l_clean)
                s = _score_name_candidate(name)
                if s >= 40:
                    candidates.append((name, s))

    if not candidates:
        return None, 0

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0], candidates[0][1]


# ==============================================================================
# DOCUMENT CLASSIFICATION & FIELD PARSER
# ==============================================================================

def parse_document_fields(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identifies document type (AADHAAR, PAN, or PASSPORT) and parses fields.
    """
    raw_text = ocr_result["raw_text"]
    lines = ocr_result["lines"]
    all_texts = ocr_result.get("all_texts", [raw_text])
    
    # Aggregate text for complete keyword coverage
    all_text_combined = raw_text + "\n" + "\n".join(all_texts)
    upper_combined = all_text_combined.upper()

    # --- 1. Detect Document Type ---
    # Passport signals: Republic of India, Passport, Type P, Country Code IND, MRZ (P<IND)
    is_passport = any(k in upper_combined for k in [
        "REPUBLIC OF INDIA", "PASSPORT", "PASSEPORT", "TYPE P", "COUNTRY CODE IND",
        "P<IND", "GIVEN NAME", "PLACE OF BIRTH", "PLACE OF ISSUE", "DATE OF EXPIRY",
        "BHARAT GANARAJYA", "भारत गणराज्य"
    ])

    is_aadhaar = any(k in upper_combined for k in [
        "AADHAAR", "UIDAI", "ENROLMENT", "MERA AADHAAR", "MERI PEHCHAN", "BHARAT SARKAR", "UNIQUE IDENTIFICATION"
    ])

    is_pan = any(k in upper_combined for k in [
        "INCOME TAX", "PERMANENT ACCOUNT NUMBER", "INCOMETAX", "ACCOUNT NUMBER CARD"
    ])

    # Regex patterns
    aadhaar_pattern = r'\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b'
    pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
    passport_pattern = r'\b[A-Z]\d{7}\b'

    has_aadhaar_num = re.search(aadhaar_pattern, all_text_combined)
    has_pan_num = re.search(pan_pattern, upper_combined)
    has_passport_num = re.search(passport_pattern, upper_combined)

    # Check for MRZ line in passport (e.g. P<IND...)
    has_mrz_line = bool(re.search(r'P\s*<\s*IND', upper_combined) or re.search(r'P<[A-Z]{3}', upper_combined))

    doc_type = "UNKNOWN"
    if is_passport or has_mrz_line:
        doc_type = "PASSPORT"
    elif is_aadhaar or (has_aadhaar_num and not is_pan):
        doc_type = "AADHAAR"
    elif is_pan or has_pan_num:
        doc_type = "PAN"
    elif has_passport_num and not has_aadhaar_num:
        doc_type = "PASSPORT"

    extracted: Dict[str, Any] = {
        "doc_type": doc_type,
        "id_number": None,
        "name": None,
        "dob": None,
        "gender": None,
        "father_name": None,
        # Passport-specific fields
        "surname": None,
        "given_names": None,
        "place_of_birth": None,
        "place_of_issue": None,
        "expiry_date": None,
        "nationality": None,
        "mrz_lines": None,
        "mrz_result": None,
        "confidence_scores": {}
    }

    ocr_data = ocr_result.get("ocr_data", [])
    def get_real_confidence(field_str: Optional[str], default_fallback: int = 80) -> int:
        if not field_str or not ocr_data:
            return default_fallback
        words = re.findall(r'[A-Za-z0-9]+', field_str)
        matched_confs = []
        for w in words:
            for item in ocr_data:
                if w.lower() == item.get("text", "").lower():
                    matched_confs.append(item.get("conf", default_fallback))
                    break
        if matched_confs:
            return int(sum(matched_confs) / len(matched_confs))
        return default_fallback

    # --- 2. Extract ID Numbers ---
    if doc_type == "AADHAAR" or (has_aadhaar_num and doc_type != "PASSPORT"):
        match = re.search(aadhaar_pattern, all_text_combined)
        if match:
            clean = re.sub(r'\s+', '', match.group(0))
            if len(clean) == 12:
                extracted["id_number"] = f"{clean[0:4]} {clean[4:8]} {clean[8:12]}"
                extracted["confidence_scores"]["id_number"] = get_real_confidence(clean, 90)

    elif doc_type == "PAN" or has_pan_num:
        match = re.search(pan_pattern, upper_combined)
        if match:
            extracted["id_number"] = match.group(0)
            extracted["confidence_scores"]["id_number"] = get_real_confidence(match.group(0), 90)

    elif doc_type == "PASSPORT" or has_passport_num:
        # Search specifically for 1 letter + 7 digits
        pp_match = re.search(r'\b([A-Z]\d{7})\b', upper_combined)
        if pp_match:
            extracted["id_number"] = pp_match.group(1)
            extracted["confidence_scores"]["id_number"] = get_real_confidence(pp_match.group(1), 92)

    # --- 3. Extract Dates (DOB & Expiry) ---
    dob_pattern = r'\b(0[1-9]|[12][0-9]|3[01])[-/.](0[1-9]|1[012])[-/.](19|20)\d\d\b'
    all_dates = list(re.finditer(dob_pattern, all_text_combined))
    
    dob_line_idx = -1
    if all_dates:
        # First date is usually DOB (or look for explicit DOB prefix)
        dob_val = all_dates[0].group(0)
        extracted["dob"] = dob_val
        extracted["confidence_scores"]["dob"] = get_real_confidence(dob_val, 85)
        for idx, l in enumerate(lines):
            if dob_val in l:
                dob_line_idx = idx
                break

    # If there are multiple dates and doc is passport, subsequent dates are Issue / Expiry
    if doc_type == "PASSPORT" and len(all_dates) >= 2:
        extracted["expiry_date"] = all_dates[-1].group(0)
        extracted["confidence_scores"]["expiry_date"] = get_real_confidence(all_dates[-1].group(0), 85)

    # --- 4. Extract Gender ---
    if re.search(r'\bFEMALE\b|\bSEX\s*[:/]?\s*F\b|महिला', upper_combined):
        extracted["gender"] = "FEMALE"
        extracted["confidence_scores"]["gender"] = 92
    elif re.search(r'\bMALE\b|\bSEX\s*[:/]?\s*M\b|पुरुष', upper_combined):
        extracted["gender"] = "MALE"
        extracted["confidence_scores"]["gender"] = 92
    elif re.search(r'\bTRANSGENDER\b', upper_combined):
        extracted["gender"] = "TRANSGENDER"
        extracted["confidence_scores"]["gender"] = 92

    # --- 5. Document Specific Parsing ---
    if doc_type == "PASSPORT":
        # Check for MRZ Lines at the bottom
        mrz_raw_lines = []
        for l in all_text_combined.split('\n'):
            l_strip = l.strip().replace(' ', '')
            if (l_strip.startswith('P<') or l_strip.startswith('P<<') or (len(l_strip) >= 35 and '<' in l_strip)):
                mrz_raw_lines.append(l_strip)

        if len(mrz_raw_lines) >= 2:
            extracted["mrz_lines"] = mrz_raw_lines[-2:]
            try:
                from validators import parse_mrz_td3
                mrz_res = parse_mrz_td3(extracted["mrz_lines"])
                extracted["mrz_result"] = mrz_res
                if mrz_res.get("full_name"):
                    extracted["name"] = mrz_res["full_name"]
                    extracted["confidence_scores"]["name"] = 95
                if mrz_res.get("surname"):
                    extracted["surname"] = mrz_res["surname"]
                if mrz_res.get("given_names"):
                    extracted["given_names"] = mrz_res["given_names"]
                if mrz_res.get("passport_number"):
                    extracted["id_number"] = mrz_res["passport_number"]
                    extracted["confidence_scores"]["id_number"] = 95
                if mrz_res.get("dob"):
                    extracted["dob"] = mrz_res["dob"]
                if mrz_res.get("sex"):
                    extracted["gender"] = mrz_res["sex"]
                if mrz_res.get("expiry_date"):
                    extracted["expiry_date"] = mrz_res["expiry_date"]
                if mrz_res.get("nationality"):
                    extracted["nationality"] = mrz_res["nationality"]
            except Exception as e:
                logger.warning(f"MRZ parser error: {e}")

        # Labeled Passport Fields Extraction
        for i, l in enumerate(lines):
            u = l.upper().strip()
            if "SURNAME" in u and i + 1 < len(lines) and not extracted["surname"]:
                cand = _clean_name_candidate(lines[i + 1])
                if cand and not _is_header_or_noise(cand):
                    extracted["surname"] = cand.upper()
            elif ("GIVEN NAME" in u or "GIVEN NAMES" in u) and i + 1 < len(lines) and not extracted["given_names"]:
                cand = _clean_name_candidate(lines[i + 1])
                if cand and not _is_header_or_noise(cand):
                    extracted["given_names"] = cand.upper()
            elif "PLACE OF BIRTH" in u and i + 1 < len(lines) and not extracted["place_of_birth"]:
                cand = _clean_name_candidate(lines[i + 1])
                if cand and not _is_header_or_noise(cand):
                    extracted["place_of_birth"] = cand.upper()
            elif "PLACE OF ISSUE" in u and i + 1 < len(lines) and not extracted["place_of_issue"]:
                cand = _clean_name_candidate(lines[i + 1])
                if cand and not _is_header_or_noise(cand):
                    extracted["place_of_issue"] = cand.upper()

        if not extracted["name"]:
            parts = []
            if extracted["given_names"]:
                parts.append(extracted["given_names"])
            if extracted["surname"]:
                parts.append(extracted["surname"])
            if parts:
                extracted["name"] = " ".join(parts)
                extracted["confidence_scores"]["name"] = 88

        if "IND" in upper_combined or "INDIAN" in upper_combined:
            extracted["nationality"] = "INDIAN"
            extracted["confidence_scores"]["nationality"] = 95

    elif doc_type == "PAN":
        for i, line in enumerate(lines):
            if "NAME" in line.upper() and i + 1 < len(lines):
                pot = _clean_name_candidate(lines[i + 1])
                if pot and len(pot) > 3 and not _is_header_or_noise(pot):
                    extracted["name"] = pot.upper()
                    extracted["confidence_scores"]["name"] = 88
            if "FATHER" in line.upper() and i + 1 < len(lines):
                pot_f = _clean_name_candidate(lines[i + 1])
                if pot_f and len(pot_f) > 3 and not _is_header_or_noise(pot_f):
                    extracted["father_name"] = pot_f.upper()
                    extracted["confidence_scores"]["father_name"] = 85

    # General Name extraction fallback (for Aadhaar or generic cards)
    if not extracted["name"]:
        best_name, _ = _extract_best_name(lines, dob_line_idx, all_texts)
        if best_name:
            extracted["name"] = best_name
            extracted["confidence_scores"]["name"] = get_real_confidence(best_name, 82)

    return extracted


# ==============================================================================
# QR CODE DETECTION & CROSS-VERIFICATION
# ==============================================================================

def detect_and_decode_qr(image_bytes: bytes) -> Dict[str, Any]:
    """Detects and decodes digital QR codes on document scan."""
    if cv2 is None:
        return {
            "qr_detected": False,
            "raw_payload": None,
            "details": "OpenCV not installed for QR detection."
        }

    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img_np = np.array(pil_img)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        detector = cv2.QRCodeDetector()
        qr_text = ""
        
        for scale in [1.0, 1.5, 0.75]:
            if scale == 1.0:
                scaled = img_bgr
            else:
                h, w = img_bgr.shape[:2]
                scaled = cv2.resize(img_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

            decoded_info, pts, _ = detector.detectAndDecode(scaled)
            if decoded_info:
                qr_text = decoded_info
                break

        if not qr_text:
            return {
                "qr_detected": False,
                "raw_payload": None,
                "parsed_data": {},
                "details": "No readable QR code payload detected on document canvas."
            }

        parsed_data: Dict[str, Any] = {}
        if "PrintLetterBarcodeData" in qr_text or "<xml" in qr_text.lower():
            uid_match = re.search(r'uid=["\'](\d+)["\']', qr_text)
            name_match = re.search(r'name=["\']([^"\']+)["\']', qr_text)
            gender_match = re.search(r'gender=["\']([^"\']+)["\']', qr_text)
            dob_match = re.search(r'dob=["\']([^"\']+)["\']', qr_text)
            yob_match = re.search(r'yob=["\']([^"\']+)["\']', qr_text)

            if uid_match:
                parsed_data["qr_id_number"] = uid_match.group(1)
            if name_match:
                parsed_data["qr_name"] = name_match.group(1)
            if gender_match:
                parsed_data["qr_gender"] = gender_match.group(1)
            if dob_match:
                parsed_data["qr_dob"] = dob_match.group(1)
            elif yob_match:
                parsed_data["qr_dob"] = f"01/01/{yob_match.group(1)}"

        return {
            "qr_detected": True,
            "raw_payload": qr_text[:120] + "..." if len(qr_text) > 120 else qr_text,
            "parsed_data": parsed_data,
            "details": f"Valid QR code payload decoded ({len(qr_text)} bytes)."
        }

    except Exception as e:
        logger.warning(f"QR decode failed: {e}")
        return {
            "qr_detected": False,
            "raw_payload": None,
            "parsed_data": {},
            "details": f"QR decoding encountered an error: {str(e)}"
        }


def cross_verify_qr(qr_result: Dict[str, Any], extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """Cross-verifies the digital QR payload against printed card text."""
    if not qr_result.get("qr_detected"):
        return {
            "qr_verified": False,
            "qr_status": "SKIPPED",
            "score": 70,
            "details": "QR code unreadable or not present on this document side."
        }

    qr_data = qr_result.get("parsed_data", {})
    ocr_name = (extracted_fields.get("name") or "").upper().strip()
    ocr_id = re.sub(r'\s+', '', str(extracted_fields.get("id_number") or ""))

    qr_name = (qr_data.get("qr_name") or "").upper().strip()
    qr_id = re.sub(r'\s+', '', str(qr_data.get("qr_id_number") or ""))

    mismatches = []
    if qr_id and ocr_id and qr_id != ocr_id:
        mismatches.append(f"ID Mismatch (Printed: {ocr_id} vs QR: {qr_id})")
    if qr_name and ocr_name and qr_name not in ocr_name and ocr_name not in qr_name:
        mismatches.append(f"Name Mismatch (Printed: '{ocr_name}' vs QR: '{qr_name}')")

    if mismatches:
        return {
            "qr_verified": False,
            "qr_status": "TAMPERED",
            "score": 0,
            "details": f"CRITICAL FORGERY: {'; '.join(mismatches)}"
        }

    return {
        "qr_verified": True,
        "qr_status": "VERIFIED",
        "score": 100,
        "details": "Digital QR payload matches printed card text."
    }
