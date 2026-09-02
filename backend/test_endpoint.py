import sys
import os
import io

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def create_sample_aadhaar_image() -> bytes:
    """Creates a sample Aadhaar-like card image for testing."""
    img = Image.new('RGB', (600, 380), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Add text
    draw.text((30, 20), "GOVERNMENT OF INDIA", fill=(0, 0, 0))
    draw.text((30, 45), "Unique Identification Authority of India", fill=(50, 50, 50))
    draw.text((30, 110), "RAJESH KUMAR SHARMA", fill=(0, 0, 0))
    draw.text((30, 145), "DOB: 14/08/1988", fill=(0, 0, 0))
    draw.text((30, 180), "MALE", fill=(0, 0, 0))
    draw.text((30, 260), "5489 2104 9811", fill=(180, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def test_extract_and_validate_endpoint():
    print("[*] Testing POST /extract-and-validate endpoint with sample Aadhaar...")
    img_bytes = create_sample_aadhaar_image()

    response = client.post(
        "/extract-and-validate",
        files={"file": ("test_aadhaar.png", img_bytes, "image/png")}
    )

    print(f" [+] Status Code: {response.status_code}")
    data = response.json()
    print(f" [+] Success: {data.get('success')} | Doc Type: {data.get('document_type')} | Verdict: {data.get('verdict')}")
    print(f" [+] Score: {data.get('authenticity_score')} | Blockchain Tx: {data.get('blockchain_anchor', {}).get('tx_hash')}")

    assert response.status_code == 200
    assert data["success"] is True
    assert "verdict" in data
    assert "authenticity_score" in data
    assert "validation_checks" in data
    assert "blockchain_anchor" in data
    print("\n[PASS] E2E Endpoint Test Passed Successfully!")

if __name__ == "__main__":
    test_extract_and_validate_endpoint()

