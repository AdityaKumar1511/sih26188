"""
Algorithmic Validators for Indian Identity Documents
- Aadhaar: Verhoeff Checksum Algorithm (D-8 Dihedral Group)
- PAN (Permanent Account Number): Income Tax Department Syntax & Rule Validator
- Passport: ICAO 9303 MRZ Check-Digit Algorithm + Syntax Validation
"""

import re
from typing import Dict, Any, Optional, List

# ==============================================================================
# VERHOEFF ALGORITHM IMPLEMENTATION (For Aadhaar 12-digit Verification)
# ==============================================================================

# Multiplication table d (dihedral group D5)
_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
]

# Permutation table p
_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]

# Inverse table inv
_VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def validate_verhoeff(num_str: str) -> bool:
    """
    Validates a number string using the Verhoeff checksum algorithm.
    Returns True if valid, False otherwise.
    """
    cleaned = re.sub(r'\s+', '', str(num_str).strip())
    if not cleaned.isdigit() or len(cleaned) == 0:
        return False

    c = 0
    reversed_digits = [int(d) for d in reversed(cleaned)]
    for i, digit in enumerate(reversed_digits):
        p_val = _VERHOEFF_P[i % 8][digit]
        c = _VERHOEFF_D[c][p_val]

    return c == 0


def generate_verhoeff_check_digit(num_str: str) -> str:
    """
    Generates the Verhoeff check digit for an 11-digit base number.
    """
    cleaned = re.sub(r'\s+', '', str(num_str).strip())
    c = 0
    reversed_digits = [int(d) for d in reversed(cleaned)]
    for i, digit in enumerate(reversed_digits):
        p_val = _VERHOEFF_P[(i + 1) % 8][digit]
        c = _VERHOEFF_D[c][p_val]
    return str(_VERHOEFF_INV[c])


def validate_aadhaar_number(aadhaar_raw: str) -> Dict[str, Any]:
    """
    Validates Indian Aadhaar Number against UIDAI rules:
    1. Exactly 12 numeric digits
    2. Must not start with 0 or 1
    3. Must pass Verhoeff checksum algorithm
    """
    cleaned = re.sub(r'[\s\-]', '', str(aadhaar_raw).strip())

    if len(cleaned) != 12 or not cleaned.isdigit():
        return {
            "is_valid": False,
            "id_number": cleaned,
            "error": f"Invalid Aadhaar length ({len(cleaned)} digits). Must be exactly 12 digits.",
            "checksum_passed": False
        }

    if cleaned[0] in ('0', '1'):
        return {
            "is_valid": False,
            "id_number": cleaned,
            "error": "Aadhaar numbers cannot start with 0 or 1 as per UIDAI specification.",
            "checksum_passed": False
        }

    checksum_passed = validate_verhoeff(cleaned)
    if not checksum_passed:
        return {
            "is_valid": False,
            "id_number": cleaned,
            "error": "Failed Verhoeff checksum verification (Tampered / Invalid check digit).",
            "checksum_passed": False
        }

    formatted = f"{cleaned[0:4]} {cleaned[4:8]} {cleaned[8:12]}"
    return {
        "is_valid": True,
        "id_number": formatted,
        "raw_number": cleaned,
        "checksum_passed": True,
        "details": "Aadhaar format and 12-digit Verhoeff checksum verified successfully."
    }


# ==============================================================================
# PAN CARD VALIDATION (Permanent Account Number)
# ==============================================================================

PAN_HOLDER_TYPES = {
    'A': 'Association of Persons (AOP)',
    'B': 'Body of Individuals (BOI)',
    'C': 'Company',
    'F': 'Firm / Limited Liability Partnership (LLP)',
    'G': 'Government Agency',
    'H': 'Hindu Undivided Family (HUF)',
    'J': 'Artificial Juridical Person',
    'L': 'Local Authority',
    'P': 'Individual / Person',
    'T': 'Trust'
}


def validate_pan_number(pan_raw: str, holder_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates Indian PAN card format against Income Tax Department standard:
    - 10 characters alphanumeric (AAAAA9999A)
    - 4th char: Entity type (P=Individual, C=Company, etc.)
    - 5th char: First character of applicant's surname / last name (if available)
    """
    cleaned = re.sub(r'[\s\-]', '', str(pan_raw).strip()).upper()

    # General Regex Pattern: 5 letters + 4 digits + 1 letter
    pan_regex = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    if not re.match(pan_regex, cleaned):
        return {
            "is_valid": False,
            "id_number": cleaned,
            "error": "Invalid PAN format. Must match standard pattern 'AAAAA9999A'.",
            "checksum_passed": False
        }

    fourth_char = cleaned[3]
    fifth_char = cleaned[4]

    holder_type = PAN_HOLDER_TYPES.get(fourth_char, "Unknown Entity")
    surname_match = None
    warning = None

    if holder_name:
        name_parts = [p for p in re.split(r'\s+', holder_name.strip().upper()) if p]
        if name_parts:
            # In Indian convention, the 5th character is typically the first letter of the last name
            expected_surname_char = name_parts[-1][0]
            surname_match = (fifth_char == expected_surname_char)
            if not surname_match:
                warning = f"5th character '{fifth_char}' does not match last name initial '{expected_surname_char}' from '{holder_name}'."

    return {
        "is_valid": True,
        "id_number": cleaned,
        "raw_number": cleaned,
        "checksum_passed": True,
        "entity_type": holder_type,
        "surname_match": surname_match,
        "warning": warning,
        "details": f"Valid PAN format. Entity Type: {holder_type}."
    }


# ==============================================================================
# INDIAN PASSPORT VALIDATION (ICAO 9303 MRZ + Syntax)
# ==============================================================================

def _icao_char_value(ch: str) -> int:
    """
    ICAO 9303 character value mapping:
    0-9 -> 0-9, A-Z -> 10-35, '<' (filler) -> 0
    """
    if ch.isdigit():
        return int(ch)
    elif ch.isalpha():
        return ord(ch.upper()) - ord('A') + 10
    else:  # '<' or any filler
        return 0


def _icao_check_digit(data: str) -> int:
    """
    Computes the ICAO 9303 check digit for a given string.
    Weighted modulo-10 algorithm with repeating weights [7, 3, 1].
    """
    weights = [7, 3, 1]
    total = 0
    for i, ch in enumerate(data):
        total += _icao_char_value(ch) * weights[i % 3]
    return total % 10


def validate_passport_number(passport_raw: str) -> Dict[str, Any]:
    """
    Validates Indian Passport Number format:
    - 1 uppercase letter (series) + 7 digits
    - Example: J8369854, K1234567
    - No mathematical checksum exists for the passport number alone;
      validation is syntax-based. MRZ check digit is computed separately.
    """
    cleaned = re.sub(r'[\s\-]', '', str(passport_raw).strip()).upper()

    passport_regex = r'^[A-Z]\d{7}$'
    if not re.match(passport_regex, cleaned):
        return {
            "is_valid": False,
            "id_number": cleaned,
            "error": f"Invalid Passport format '{cleaned}'. Must be 1 letter + 7 digits (e.g., J8369854).",
            "checksum_passed": False
        }

    series_letter = cleaned[0]
    return {
        "is_valid": True,
        "id_number": cleaned,
        "raw_number": cleaned,
        "checksum_passed": True,  # Syntax validation passed
        "series": series_letter,
        "details": f"Valid Indian Passport syntax (Series {series_letter}). Format: {series_letter}NNNNNNN."
    }


def parse_mrz_td3(mrz_lines: List[str]) -> Dict[str, Any]:
    """
    Parses a TD3 (passport) Machine Readable Zone per ICAO 9303 Part 4.
    
    TD3 MRZ has 2 lines of 44 characters each:
    
    Line 1: P<INDSURNAME<<GIVENNAME<GIVENNAME<<<<<<<<<<<<
      [0]     = Document type ('P')
      [1]     = Type modifier ('<' = standard)
      [2:5]   = Issuing state code (e.g., 'IND')
      [5:44]  = Name field: SURNAME<<GIVEN<NAMES padded with '<'
    
    Line 2: J83698541IND8501011M2501015<<<<<<<<<<<<<<04
      [0:9]   = Passport number (may contain '<' padding)
      [9]     = Check digit for passport number
      [10:13] = Nationality (e.g., 'IND')
      [13:19] = Date of birth (YYMMDD)
      [19]    = Check digit for DOB
      [20]    = Sex (M/F/<)
      [21:27] = Date of expiry (YYMMDD)
      [27]    = Check digit for expiry
      [28:42] = Personal number / optional data
      [42]    = Check digit for personal number
      [43]    = Composite check digit (over positions 0-9, 13-19, 21-27, 28-42 of line 2)
    """
    result = {
        "valid": False,
        "passport_number": None,
        "surname": None,
        "given_names": None,
        "full_name": None,
        "nationality": None,
        "dob": None,
        "sex": None,
        "expiry_date": None,
        "issuing_country": None,
        "check_digits": {},
        "errors": [],
        "details": ""
    }

    if len(mrz_lines) < 2:
        result["errors"].append("MRZ requires 2 lines of 44 characters each.")
        result["details"] = "Incomplete MRZ — fewer than 2 lines detected."
        return result

    line1 = mrz_lines[0].strip().replace(' ', '')
    line2 = mrz_lines[1].strip().replace(' ', '')

    # Normalize: replace common OCR errors in MRZ
    line1 = line1.replace('0', 'O') if line1.startswith('P') else line1  # Don't replace in line2
    
    if len(line1) < 44 or len(line2) < 44:
        # Try to pad if close
        line1 = line1.ljust(44, '<')
        line2 = line2.ljust(44, '<')

    # --- Parse Line 1 ---
    doc_type = line1[0]
    if doc_type != 'P':
        result["errors"].append(f"Document type '{doc_type}' is not a passport (expected 'P').")

    issuing_country = line1[2:5].replace('<', '')
    result["issuing_country"] = issuing_country

    # Parse name: SURNAME<<GIVEN<NAMES<<<
    name_field = line1[5:44]
    name_parts = name_field.split('<<')
    surname = name_parts[0].replace('<', ' ').strip() if len(name_parts) > 0 else ""
    given_names = name_parts[1].replace('<', ' ').strip() if len(name_parts) > 1 else ""
    
    result["surname"] = surname
    result["given_names"] = given_names
    result["full_name"] = f"{given_names} {surname}".strip()

    # --- Parse Line 2 ---
    passport_num = line2[0:9].replace('<', '')
    result["passport_number"] = passport_num

    nationality = line2[10:13].replace('<', '')
    result["nationality"] = nationality

    # DOB (YYMMDD)
    dob_raw = line2[13:19]
    if dob_raw.replace('<', '').isdigit() and len(dob_raw) == 6:
        yy, mm, dd = dob_raw[0:2], dob_raw[2:4], dob_raw[4:6]
        year = int(yy)
        century = "19" if year > 30 else "20"  # Heuristic: >30 = 1900s
        result["dob"] = f"{dd}/{mm}/{century}{yy}"

    # Sex
    sex_char = line2[20]
    result["sex"] = {"M": "MALE", "F": "FEMALE"}.get(sex_char, "UNSPECIFIED")

    # Expiry date (YYMMDD)
    exp_raw = line2[21:27]
    if exp_raw.replace('<', '').isdigit() and len(exp_raw) == 6:
        yy, mm, dd = exp_raw[0:2], exp_raw[2:4], exp_raw[4:6]
        century = "20"  # Expiry dates are always in 2000s for current passports
        result["expiry_date"] = f"{dd}/{mm}/{century}{yy}"

    # --- Verify Check Digits ---
    all_passed = True

    # Check digit 1: Passport number (positions 0-8, check at 9)
    try:
        expected_pp = int(line2[9])
        computed_pp = _icao_check_digit(line2[0:9])
        pp_ok = (expected_pp == computed_pp)
        result["check_digits"]["passport_number"] = {"expected": expected_pp, "computed": computed_pp, "passed": pp_ok}
        if not pp_ok:
            result["errors"].append(f"Passport number check digit FAILED (expected {expected_pp}, got {computed_pp}).")
            all_passed = False
    except (ValueError, IndexError):
        result["errors"].append("Could not parse passport number check digit.")
        all_passed = False

    # Check digit 2: DOB (positions 13-18, check at 19)
    try:
        expected_dob = int(line2[19])
        computed_dob = _icao_check_digit(line2[13:19])
        dob_ok = (expected_dob == computed_dob)
        result["check_digits"]["dob"] = {"expected": expected_dob, "computed": computed_dob, "passed": dob_ok}
        if not dob_ok:
            result["errors"].append(f"DOB check digit FAILED (expected {expected_dob}, got {computed_dob}).")
            all_passed = False
    except (ValueError, IndexError):
        result["errors"].append("Could not parse DOB check digit.")
        all_passed = False

    # Check digit 3: Expiry date (positions 21-26, check at 27)
    try:
        expected_exp = int(line2[27])
        computed_exp = _icao_check_digit(line2[21:27])
        exp_ok = (expected_exp == computed_exp)
        result["check_digits"]["expiry"] = {"expected": expected_exp, "computed": computed_exp, "passed": exp_ok}
        if not exp_ok:
            result["errors"].append(f"Expiry date check digit FAILED (expected {expected_exp}, got {computed_exp}).")
            all_passed = False
    except (ValueError, IndexError):
        result["errors"].append("Could not parse expiry check digit.")
        all_passed = False

    # Check digit 4: Composite (positions 0-9 + 13-19 + 21-27 + 28-42 of line2, check at 43)
    try:
        composite_str = line2[0:10] + line2[13:20] + line2[21:28] + line2[28:43]
        expected_comp = int(line2[43])
        computed_comp = _icao_check_digit(composite_str)
        comp_ok = (expected_comp == computed_comp)
        result["check_digits"]["composite"] = {"expected": expected_comp, "computed": computed_comp, "passed": comp_ok}
        if not comp_ok:
            result["errors"].append(f"Composite check digit FAILED (expected {expected_comp}, got {computed_comp}).")
            all_passed = False
    except (ValueError, IndexError):
        result["errors"].append("Could not parse composite check digit.")
        all_passed = False

    result["valid"] = all_passed

    if all_passed:
        passed_count = sum(1 for v in result["check_digits"].values() if v.get("passed"))
        result["details"] = f"MRZ verified: All {passed_count} ICAO 9303 check digits passed. Name: {result['full_name']}, PP#: {passport_num}."
    else:
        failed = [k for k, v in result["check_digits"].items() if not v.get("passed")]
        result["details"] = f"MRZ check digit FAILURE on: {', '.join(failed)}. Possible forgery or OCR error in MRZ zone."

    return result
