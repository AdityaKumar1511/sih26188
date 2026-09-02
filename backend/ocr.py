"""
OCR & Information Extraction Module for Identity Documents
Supports fast multi-pass OCR via OpenCV and Pytesseract / EasyOCR.
Extracts Aadhaar, PAN, and Indian Passport with high precision and watermark filtering.
"""

import io
import os
import re
import shutil
import logging
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageOps
import numpy as np

logger = logging.getLogger(__name__)

# Optional dependencies (OpenCV, Pytesseract, EasyOCR)
try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None

try:
    import pytesseract  # type: ignore
    # Auto-detect Tesseract executable path on Windows, Linux, and macOS
    _tesseract_candidates = [
        os.environ.get("TESSERACT_CMD"),
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        r"C:\tools\tesseract\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    ]
    for _t_cmd in _tesseract_candidates:
        if _t_cmd and os.path.exists(_t_cmd):
            pytesseract.tesseract_cmd = _t_cmd
            pytesseract.pytesseract.tesseract_cmd = _t_cmd
            _tess_dir = os.path.dirname(_t_cmd)
            if _tess_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = _tess_dir + os.pathsep + os.environ.get("PATH", "")
            _tessdata_path = os.path.join(_tess_dir, "tessdata")
            if os.path.exists(_tessdata_path) and "TESSDATA_PREFIX" not in os.environ:
                os.environ["TESSDATA_PREFIX"] = _tessdata_path
            logger.info(f"Tesseract OCR configured at: {_t_cmd}")
            break
except ImportError:
    pytesseract = None

_easyocr_reader: Optional[Any] = None


def get_easyocr_reader() -> Any:
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr  # type: ignore
            _easyocr_reader = easyocr.Reader(['en', 'hi'], gpu=False)
        except Exception as e:
            logger.debug(f"EasyOCR reader init skipped or failed: {e}")
    return _easyocr_reader


def preprocess_image(image_bytes: bytes) -> List[Tuple[str, Image.Image]]:
    """
    Applies optimized, high-performance image enhancement pipelines.
    Handles EXIF orientation, contrast stretching, CLAHE, adaptive thresholding, and denoising.
    """
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image = ImageOps.exif_transpose(pil_image)
        pil_image = pil_image.convert("RGB")
    except Exception:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    results: List[Tuple[str, Image.Image]] = [("raw", pil_image)]

    if cv2 is None:
        return results

    open_cv_image = np.array(pil_image)
    open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

    # 1. Resize if image is too small or excessively large
    h, w = open_cv_image.shape[:2]
    if w < 1200:
        scale_factor = 1200 / max(w, 1)
        open_cv_image = cv2.resize(
            open_cv_image,
            (int(w * scale_factor), int(h * scale_factor)),
            interpolation=cv2.INTER_CUBIC
        )
    elif w > 3200:
        scale_factor = 2400 / w
        open_cv_image = cv2.resize(
            open_cv_image,
            (int(w * scale_factor), int(h * scale_factor)),
            interpolation=cv2.INTER_AREA
        )

    # 2. Grayscale & CLAHE (Contrast-Limited Adaptive Histogram Equalization)
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    clahe_img = clahe.apply(gray)
    results.append(("clahe", Image.fromarray(clahe_img)))

    # 3. Bilateral Filter Denoised + CLAHE (Sharp text contours without background noise)
    denoised = cv2.bilateralFilter(clahe_img, 9, 75, 75)
    results.append(("denoised", Image.fromarray(denoised)))

    # 4. Adaptive Threshold (for crisp text contours)
    thresh = cv2.adaptiveThreshold(
        clahe_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
    )
    results.append(("threshold", Image.fromarray(thresh)))

    # 5. Otsu thresholding (good for MRZ and high-contrast lines)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results.append(("otsu", Image.fromarray(otsu)))

    return results


def perform_ocr(image_bytes: bytes) -> Dict[str, Any]:
    """
    Executes fast, targeted multi-pass OCR on document image.
    Uses PSM 6 (uniform block) and PSM 3 (auto page segmentation).
    """
    preprocessed_images = preprocess_image(image_bytes)
    raw_pil = preprocessed_images[0][1]

    best_text = ""
    all_texts: List[str] = []
    ocr_data = []
    engine_used = "none"

    if pytesseract is not None:
        try:
            txt1, txt2, txt3 = "", "", ""
            # Pass 1: CLAHE image with PSM 6 (best for identity card layouts)
            clahe_img = next((img for label, img in preprocessed_images if label == "clahe"), raw_pil)
            txt1 = pytesseract.image_to_string(clahe_img, lang='eng', config='--psm 6').strip()
            
            pass1_ocr_data = []
            avg_word_conf = 0.0
            if txt1:
                all_texts.append(txt1)
                best_text = txt1
                engine_used = "tesseract"

                # Extract word bounding boxes and confidences from CLAHE image
                try:
                    data_dict = pytesseract.image_to_data(clahe_img, output_type=pytesseract.Output.DICT)
                    word_confs = []
                    for i in range(len(data_dict['text'])):
                        t = data_dict['text'][i].strip()
                        conf = int(data_dict['conf'][i])
                        if t and conf > 15:
                            pass1_ocr_data.append({
                                "text": t,
                                "conf": conf,
                                "left": data_dict['left'][i],
                                "top": data_dict['top'][i],
                                "width": data_dict['width'][i],
                                "height": data_dict['height'][i]
                            })
                            word_confs.append(conf)
                    if word_confs:
                        avg_word_conf = sum(word_confs) / len(word_confs)
                except Exception as e:
                    logger.debug(f"image_to_data error in Pass 1: {e}")

            ocr_data = pass1_ocr_data

            # Early Exit Check: If Pass 1 produced substantial text with high confidence, skip Passes 2 & 3
            if len(txt1) > 40 and avg_word_conf >= 70:
                logger.info(
                    f"OCR Pass 1 produced clean result ({len(txt1)} chars, avg conf: {avg_word_conf:.1f}%). "
                    f"Early exit triggered — skipping Passes 2 & 3."
                )
            else:
                logger.info(
                    f"OCR Pass 1 result ({len(txt1)} chars, avg conf: {avg_word_conf:.1f}%) below threshold. "
                    f"Executing multi-pass OCR (Passes 2 & 3)."
                )
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
                            engine_used = "tesseract"

                # If a later pass yielded the best text, extract word boxes from that image
                if best_text and (not ocr_data or best_text != txt1):
                    try:
                        target_img = thresh_img if (thresh_img is not None and best_text == txt3) else (raw_pil if best_text == txt2 else clahe_img)
                        data_dict = pytesseract.image_to_data(target_img, output_type=pytesseract.Output.DICT)
                        new_ocr_data = []
                        for i in range(len(data_dict['text'])):
                            t = data_dict['text'][i].strip()
                            conf = int(data_dict['conf'][i])
                            if t and conf > 15:
                                new_ocr_data.append({
                                    "text": t,
                                    "conf": conf,
                                    "left": data_dict['left'][i],
                                    "top": data_dict['top'][i],
                                    "width": data_dict['width'][i],
                                    "height": data_dict['height'][i]
                                })
                        if new_ocr_data:
                            ocr_data = new_ocr_data
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

_NOISE_STEMS = (
    "GOVERN", "INDIA", "AUTHOR", "AADHAAR", "ADHAR", "UIDAI", "UNIQUE",
    "IDENTIF", "INCOME", "TAX", "BHARAT", "SARKAR", "PEHCHAN", "ENROL",
    "PASSPORT", "REPUBLIC", "MINISTRY", "EXTERNAL", "AFFAIRS", "DEPARTMENT",
    "ACCOUNT", "MERA", "DOWNLOAD", "LETTER", "HELP", "WWW", "HTTP", "COM",
    "MALE", "FEMALE", "DOB", "YEAR", "BIRTH", "SIGNATURE", "HOLDER", "PROOF",
    "CITIZEN", "VERIF", "AUTHENTIC", "QR", "XML", "OFFLINE", "SCAN", "TOLL",
    "FREE", "1947", "SAMPLE", "SPECIMEN", "WATERMARK", "STOCK", "SHUTTER",
    "GETTY", "ALAMY", "DEPOSIT", "DREAMS", "ILLUSTRAT", "VECTOR", "OVERLAY",
    "CANVAS", "SCREENING", "FATHER", "HUSBAND", "MOTHER", "GUARDIAN", "CARE"
)

_NOISE_KEYWORDS = frozenset([
    "GOVERNMENT", "INDIA", "AUTHORITY", "AADHAAR", "UIDAI", "ISSUE",
    "UNIQUE", "IDENTIFICATION", "PRINT", "ADDRESS", "MERA", "PEHCHAN",
    "ENROLMENT", "ENROLLMENT", "INCOME", "TAX", "PERMANENT", "ACCOUNT",
    "DEPARTMENT", "BHARAT", "SARKAR", "VID", "VALID", "DOWNLOAD",
    "GENERATED", "LETTER", "DATE", "HELP", "WWW", "HTTP", "COM",
    "MALE", "FEMALE", "DOB", "YEAR", "BIRTH", "SIGNATURE", "HOLDER",
    "FATHER", "FATHER'S", "HUSBAND", "HUSBAND'S", "MOTHER", "GUARDIAN",
    "CARE", "S/O", "D/O", "W/O", "C/O", "SO", "DO", "WO", "CO",
    "POST", "DISTRICT", "STATE", "PIN", "PINCODE", "PO", "VILLAGE",
    "ROAD", "STREET", "FLAT", "HOUSE", "BUILDING", "NAGAR", "COLONY",
    "PASSPORT", "REPUBLIC", "NATIONALITY", "INDIAN", "HYDERABAD",
    "SURNAME", "GIVEN", "NAME", "NAMES", "SEX", "CODE", "TYPE",
    "COUNTRY", "PASSEPORT", "MINISTRY", "EXTERNAL", "AFFAIRS",
    "REGIONAL", "OFFICE", "OFFICER", "ASSISTANT", "FILE", "NO",
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
    if re.search(r'\.(COM|ORG|NET|IN|GOV|EDU|IO|CO|XYZ)\b', upper) or "HTTP" in upper or "WWW." in upper or "@" in upper:
        return True

    # Reject noise stems anywhere in the line (handles OCR corrupted headers like Emgovernment, Indiawerr)
    if any(stem in upper for stem in _NOISE_STEMS):
        return True

    # Reject relative markers: S/O, D/O, W/O, C/O
    if re.search(r'\b(S/O|D/O|W/O|C/O|SO|DO|WO|CO|FATHER|HUSBAND|MOTHER|GUARDIAN)\b', upper):
        return True

    words = [w.strip('.,:-/()[]{}') for w in upper.split() if w.strip('.,:-/()[]{}')]
    if not words:
        return True

    noise_count = sum(1 for w in words if w in _NOISE_KEYWORDS or any(stem in w for stem in _NOISE_STEMS))
    if noise_count / len(words) >= 0.3:
        return True

    # Reject lines that are mostly numeric
    digit_count = sum(1 for ch in text if ch.isdigit())
    if digit_count / len(text) > 0.3:
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
            w_upper = w_clean.upper()
            if w_upper not in _NOISE_KEYWORDS and not any(stem in w_upper for stem in _NOISE_STEMS):
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
        score += 40
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

    # 1. Line immediately before DOB (strongest Aadhaar signal)
    if dob_line_idx > 0:
        for offset in [1, 2, 3, 4]:
            idx = dob_line_idx - offset
            if 0 <= idx < len(lines):
                raw_line = lines[idx]
                if not _is_header_or_noise(raw_line):
                    name = _clean_name_candidate(raw_line)
                    if name and not _is_header_or_noise(name):
                        s = _score_name_candidate(name)
                        if s > 0:
                            candidates.append((name, s + 60 - (offset * 5)))

    # 2. Lines following explicit Name / Given Name labels
    for i, line in enumerate(lines):
        upper = line.upper().strip()
        name_label_match = re.search(r'\b(?:NAME|FULL\s*NAME|GIVEN\s*NAME|GIVEN\s*NAMES|नाम)\s*[:\-]?\s*(.+)', upper)
        if name_label_match:
            cand_inline = _clean_name_candidate(name_label_match.group(1))
            if cand_inline and not _is_header_or_noise(cand_inline):
                s_inline = _score_name_candidate(cand_inline)
                if s_inline > 0:
                    candidates.append((cand_inline, s_inline + 50))

        if re.search(r'\b(GIVEN\s*NAME|GIVEN\s*NAMES|NAME|FULL\s*NAME|नाम)\b', upper):
            if i + 1 < len(lines):
                raw = lines[i + 1]
                if not _is_header_or_noise(raw):
                    name = _clean_name_candidate(raw)
                    if name and not _is_header_or_noise(name):
                        s = _score_name_candidate(name)
                        if s > 0:
                            candidates.append((name, s + 45))

    # 3. Consensus across all OCR passes
    for txt in all_texts:
        for l in txt.split('\n'):
            l_clean = l.strip()
            if not _is_header_or_noise(l_clean):
                name = _clean_name_candidate(l_clean)
                if name and not _is_header_or_noise(name):
                    s = _score_name_candidate(name)
                    if s >= 40:
                        candidates.append((name, s))

    if not candidates:
        return None, 0

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0], candidates[0][1]


# ==============================================================================
# OCR ERROR REPAIR HELPERS
# ==============================================================================

def _repair_aadhaar_ocr(raw_text: str) -> Optional[str]:
    """
    Attempts to detect and repair 12-digit Aadhaar candidates with common OCR digit confusions.
    Verifies with Verhoeff checksum if available.
    """
    from validators import validate_verhoeff

    # Standard pattern
    standard_match = re.search(r'\b([2-9]\d{3})\s?(\d{4})\s?(\d{4})\b', raw_text)
    if standard_match:
        digits = "".join(standard_match.groups())
        if len(digits) == 12 and validate_verhoeff(digits):
            return f"{digits[0:4]} {digits[4:8]} {digits[8:12]}"

    # Look for 12-char alphanumeric tokens that could be OCR-corrupted Aadhaar
    char_to_digit = {'O': '0', 'o': '0', 'D': '0', 'I': '1', 'l': '1', '|': '1', 'Z': '2', 'z': '2', 'S': '5', 's': '5', 'B': '8'}
    tokens = re.findall(r'[0-9A-Za-z|]{4}[\s\-]?[0-9A-Za-z|]{4}[\s\-]?[0-9A-Za-z|]{4}', raw_text)
    for token in tokens:
        cleaned = re.sub(r'[\s\-]', '', token)
        if len(cleaned) == 12:
            repaired = "".join(char_to_digit.get(ch, ch) for ch in cleaned)
            if repaired.isdigit() and repaired[0] not in ('0', '1'):
                if validate_verhoeff(repaired):
                    return f"{repaired[0:4]} {repaired[4:8]} {repaired[8:12]}"

    if standard_match:
        digits = "".join(standard_match.groups())
        return f"{digits[0:4]} {digits[4:8]} {digits[8:12]}"

    return None


def _repair_pan_ocr(raw_text: str) -> Optional[str]:
    """
    Detects and repairs 10-character PAN cards: 5 letters, 4 digits, 1 letter (e.g. ABCPE1234F).
    """
    # 1. Exact regex match
    match = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', raw_text.upper())
    if match:
        return match.group(1)

    # 2. Fuzzy repair for 10-character alphanumeric tokens
    digit_to_char = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B'}
    char_to_digit = {'O': '0', 'I': '1', 'l': '1', 'Z': '2', 'S': '5', 'B': '8', 'D': '0'}

    tokens = re.findall(r'\b[A-Za-z0-9]{10}\b', raw_text)
    for token in tokens:
        token_upper = token.upper()
        # Positions 0-4: must be letters
        part1 = "".join(digit_to_char.get(ch, ch) for ch in token_upper[:5])
        # Positions 5-8: must be digits
        part2 = "".join(char_to_digit.get(ch, ch) for ch in token_upper[5:9])
        # Position 9: must be letter
        part3 = digit_to_char.get(token_upper[9], token_upper[9])

        candidate = f"{part1}{part2}{part3}"
        if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', candidate):
            if candidate[3] in "CPHFATBLJG":
                return candidate

    return None


def _repair_passport_ocr(raw_text: str) -> Optional[str]:
    """
    Detects and repairs 8-character Indian Passport number: 1 letter + 7 digits (e.g. Z1234567).
    """
    upper = raw_text.upper()

    digit_to_char = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B', '7': 'T', '6': 'G'}
    char_to_digit = {'O': '0', 'I': '1', 'l': '1', 'Z': '2', 'S': '5', 'B': '8', 'D': '0'}

    # 1. Label match (PASSPORT NO / PASSPORT NUMBER)
    label_match = re.search(r'PASSPORT\s*(?:NO|NUMBER)?[\s\.\:\-]*([A-Z0-9]{8})\b', upper)
    if label_match:
        cand = label_match.group(1)
        first_char = digit_to_char.get(cand[0], cand[0])
        rest_digits = "".join(char_to_digit.get(ch, ch) for ch in cand[1:])
        fixed = f"{first_char}{rest_digits}"
        if re.match(r'^[A-Z]\d{7}$', fixed):
            return fixed

    # 2. Exact standard format (1 letter + 7 digits)
    match = re.search(r'\b([A-Z]\d{7})\b', upper)
    if match:
        return match.group(1)

    # 3. Fuzzy repair for 8-char tokens
    tokens = re.findall(r'\b[A-Za-z0-9]{8}\b', upper)
    for token in tokens:
        first = digit_to_char.get(token[0], token[0])
        rest = "".join(char_to_digit.get(ch, ch) for ch in token[1:])
        candidate = f"{first}{rest}"
        if re.match(r'^[A-Z]\d{7}$', candidate):
            return candidate

    return None


def _parse_dob(all_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts Date of Birth (and Expiry Date if present) across multiple formats:
    - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    - YYYY-MM-DD, YYYY/MM/DD
    - DD Mon YYYY / DD Month YYYY (e.g. 14 Aug 1988)
    - Year of Birth: YYYY / जन्म वर्ष: YYYY
    """
    dob_val = None
    expiry_val = None

    # Standard numeric date: DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY (allows optional spaces around separators)
    d_regex = r'\b(0?[1-9]|[12][0-9]|3[01])\s*[\/\-\.]\s*(0?[1-9]|1[012])\s*[\/\-\.]\s*(19\d\d|20\d\d)\b'
    matches = list(re.finditer(d_regex, all_text))
    if matches:
        first_m = matches[0]
        d_str = first_m.group(1).zfill(2)
        m_str = first_m.group(2).zfill(2)
        y_str = first_m.group(3)
        dob_val = f"{d_str}/{m_str}/{y_str}"
        if len(matches) >= 2:
            sec_m = matches[-1]
            d_sec = sec_m.group(1).zfill(2)
            m_sec = sec_m.group(2).zfill(2)
            y_sec = sec_m.group(3)
            expiry_val = f"{d_sec}/{m_sec}/{y_sec}"

    # Textual month format: 14 Aug 1988 or 14-Aug-1988 or 14 August 1988
    if not dob_val:
        month_map = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
            'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12',
            'JANUARY': '01', 'FEBRUARY': '02', 'MARCH': '03', 'APRIL': '04', 'JUNE': '06',
            'JULY': '07', 'AUGUST': '08', 'SEPTEMBER': '09', 'OCTOBER': '10', 'NOVEMBER': '11', 'DECEMBER': '12'
        }
        text_d_regex = r'\b(0?[1-9]|[12][0-9]|3[01])[\s\-\/\.]([A-Za-z]{3,9})[\s\-\/\.](19\d\d|20\d\d)\b'
        t_matches = list(re.finditer(text_d_regex, all_text))
        for tm in t_matches:
            mon_str = tm.group(2).upper()
            if mon_str in month_map:
                day_str = tm.group(1).zfill(2)
                dob_val = f"{day_str}/{month_map[mon_str]}/{tm.group(3)}"
                break

    # Year of birth only fallback: e.g. Year of Birth: 1988 or YOB : 1988 or जन्म वर्ष: 1988
    if not dob_val:
        yob_match = re.search(r'(?:YEAR\s*OF\s*BIRTH|YOB|DOB|जन्म\s*वर्ष|जन्म\s*तिथि)\s*[:\-]?\s*(19\d\d|20\d\d)', all_text, re.IGNORECASE)
        if yob_match:
            dob_val = f"01/01/{yob_match.group(1)}"

    return dob_val, expiry_val


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
    is_passport = any(k in upper_combined for k in [
        "REPUBLIC OF INDIA", "PASSPORT", "PASSEPORT", "TYPE P", "COUNTRY CODE IND",
        "P<IND", "GIVEN NAME", "PLACE OF BIRTH", "PLACE OF ISSUE", "DATE OF EXPIRY",
        "BHARAT GANARAJYA", "भारत गणराज्य"
    ])

    is_aadhaar = any(k in upper_combined for k in [
        "AADHAAR", "UIDAI", "ENROLMENT", "MERA AADHAAR", "MERI PEHCHAN", "BHARAT SARKAR", "UNIQUE IDENTIFICATION",
        "आम आदमी का अधिकार", "भारत सरकार"
    ])

    is_pan = any(k in upper_combined for k in [
        "INCOME TAX", "PERMANENT ACCOUNT NUMBER", "INCOMETAX", "ACCOUNT NUMBER CARD", "आयकर विभाग", "PAN CARD"
    ])

    # Check for repaired ID numbers
    repaired_aadhaar = _repair_aadhaar_ocr(all_text_combined)
    repaired_pan = _repair_pan_ocr(all_text_combined)
    repaired_passport = _repair_passport_ocr(all_text_combined)

    # Check for MRZ line in passport (e.g. P<IND...)
    has_mrz_line = bool(re.search(r'P\s*[<c«\(]\s*IND', upper_combined) or re.search(r'P[<c«\(][A-Z]{3}', upper_combined))

    doc_type = "UNKNOWN"
    if is_passport or has_mrz_line:
        doc_type = "PASSPORT"
    elif is_aadhaar or (repaired_aadhaar and not is_pan):
        doc_type = "AADHAAR"
    elif is_pan or repaired_pan:
        doc_type = "PAN"
    elif repaired_passport and not repaired_aadhaar:
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
    if doc_type == "AADHAAR" or (repaired_aadhaar and doc_type != "PASSPORT"):
        if repaired_aadhaar:
            extracted["id_number"] = repaired_aadhaar
            extracted["confidence_scores"]["id_number"] = get_real_confidence(repaired_aadhaar, 92)

    elif doc_type == "PAN" or repaired_pan:
        if repaired_pan:
            extracted["id_number"] = repaired_pan
            extracted["confidence_scores"]["id_number"] = get_real_confidence(repaired_pan, 92)

    elif doc_type == "PASSPORT" or repaired_passport:
        if repaired_passport:
            extracted["id_number"] = repaired_passport
            extracted["confidence_scores"]["id_number"] = get_real_confidence(repaired_passport, 92)

    # --- 3. Extract Dates (DOB & Expiry) ---
    parsed_dob, parsed_expiry = _parse_dob(all_text_combined)
    dob_line_idx = -1
    if parsed_dob:
        extracted["dob"] = parsed_dob
        extracted["confidence_scores"]["dob"] = get_real_confidence(parsed_dob, 88)
        dob_digits = re.sub(r'[^0-9]', '', parsed_dob)
        for idx, l in enumerate(lines):
            clean_digits = re.sub(r'[^0-9]', '', l)
            if (
                parsed_dob in l
                or (parsed_dob[:2] in l and parsed_dob[-4:] in l)
                or (len(dob_digits) >= 4 and dob_digits[-4:] in clean_digits)
                or re.search(r'\b(DOB|BIRTH|जन्म\s*तिथि|जन्म\s*वर्ष)\b', l, re.IGNORECASE)
            ):
                dob_line_idx = idx
                break

    if parsed_expiry and doc_type == "PASSPORT":
        extracted["expiry_date"] = parsed_expiry
        extracted["confidence_scores"]["expiry_date"] = get_real_confidence(parsed_expiry, 85)

    # --- 4. Extract Gender ---
    if re.search(r'\bFEMALE\b|\bSEX\s*[:/]?\s*F\b|महिला|FEMALE/महिला|FEMALE\s*/\s*महिला|स्त्री', upper_combined):
        extracted["gender"] = "FEMALE"
        extracted["confidence_scores"]["gender"] = 92
    elif re.search(r'\bMALE\b|\bSEX\s*[:/]?\s*M\b|पुरुष|MALE/पुरुष|MALE\s*/\s*पुरुष', upper_combined):
        extracted["gender"] = "MALE"
        extracted["confidence_scores"]["gender"] = 92
    elif re.search(r'\bTRANSGENDER\b|ट्रांसजेंडर', upper_combined):
        extracted["gender"] = "TRANSGENDER"
        extracted["confidence_scores"]["gender"] = 92

    # --- 5. Document Specific Parsing ---
    if doc_type == "PASSPORT":
        # Check for MRZ Lines at the bottom
        mrz_raw_lines = []
        for l in all_text_combined.split('\n'):
            l_strip = l.strip().replace(' ', '')
            l_clean_chevrons = re.sub(r'[c«‹\(\[\{]', '<', l_strip)
            if (l_clean_chevrons.startswith('P<') or l_clean_chevrons.startswith('P<<') or (len(l_clean_chevrons) >= 35 and '<' in l_clean_chevrons)):
                mrz_raw_lines.append(l_clean_chevrons)

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
                    # Validate and repair MRZ passport number if needed
                    repaired_mrz_num = _repair_passport_ocr(mrz_res["passport_number"])
                    if repaired_mrz_num:
                        extracted["id_number"] = repaired_mrz_num
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

        if not extracted["name"] or "<" in str(extracted.get("name", "")):
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
            upper_l = line.upper()
            if "NAME" in upper_l and "FATHER" not in upper_l and i + 1 < len(lines):
                pot = _clean_name_candidate(lines[i + 1])
                if pot and len(pot) > 3 and not _is_header_or_noise(pot):
                    extracted["name"] = pot.upper()
                    extracted["confidence_scores"]["name"] = 88
            if "FATHER" in upper_l and i + 1 < len(lines):
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
