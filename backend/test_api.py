"""
Unit Tests for Algorithmic Validators & OCR Parsers
Run with: python backend/test_api.py
"""

from validators import validate_verhoeff, validate_aadhaar_number, validate_pan_number

def test_validators():
    print("Testing Aadhaar Verhoeff Checksum...")
    
    # Valid Aadhaar numbers with correct Verhoeff check digits
    valid_aadhaar = "548921049811"
    res1 = validate_aadhaar_number(valid_aadhaar)
    assert res1["is_valid"] is True, f"Expected valid for {valid_aadhaar}"
    assert res1["checksum_passed"] is True
    print(f" [✓] Valid Aadhaar passed: {valid_aadhaar}")

    # Tampered / Invalid Aadhaar (last digit changed from 1 to 9)
    invalid_aadhaar = "548921049819"
    res2 = validate_aadhaar_number(invalid_aadhaar)
    assert res2["is_valid"] is False, f"Expected invalid for {invalid_aadhaar}"
    assert res2["checksum_passed"] is False
    print(f" [✓] Tampered Aadhaar caught: {invalid_aadhaar} -> {res2['error']}")

    # Invalid starting digit (starts with 0 or 1)
    bad_prefix = "048921049812"
    res3 = validate_aadhaar_number(bad_prefix)
    assert res3["is_valid"] is False
    print(f" [✓] Bad prefix Aadhaar caught: {bad_prefix} -> {res3['error']}")

    print("\nTesting PAN Card Validation...")
    
    # Valid PAN with matching surname
    valid_pan = "ABCPE1234F"
    p_res1 = validate_pan_number(valid_pan, holder_name="VIKRAM SINGH MEHTA")
    assert p_res1["is_valid"] is True
    assert p_res1["entity_type"] == "Individual / Person"  # 4th char is P
    # 5th char is E; surname is Mehta (M), so surname_match is False with warning
    assert p_res1["surname_match"] is False
    print(f" [✓] Valid PAN format checked: {valid_pan} (Warning caught: {p_res1['warning']})")

    # PAN with matching surname
    pan_matching = "BKZPS8491K"
    p_res2 = validate_pan_number(pan_matching, holder_name="PRIYA SHARMA")
    assert p_res2["is_valid"] is True
    assert p_res2["surname_match"] is True
    print(f" [✓] PAN with matching surname initial passed: {pan_matching} (5th char 'S' matches 'SHARMA')")

    # Invalid PAN format
    bad_pan = "ABCD12345F"
    p_res3 = validate_pan_number(bad_pan)
    assert p_res3["is_valid"] is False
    print(f" [✓] Malformed PAN rejected: {bad_pan}")

    print("\n[ALL VALIDATION TESTS PASSED SUCCESSFULLY!]")


if __name__ == "__main__":
    test_validators()
