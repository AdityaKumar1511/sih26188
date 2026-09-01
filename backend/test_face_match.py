"""
Unit & Integration Tests for Biometric Face Matching Engine (SIH PS 26188)
Run with: ./venv/bin/python test_face_match.py
"""

import io
import cv2
import numpy as np
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from main import app
from face_matcher import detect_face, compute_passive_liveness, match_faces_1to1

client = TestClient(app)


def generate_synthetic_face_image(skin_tone=(210, 160, 130), eye_offset=0, smile=True) -> bytes:
    """Generates a synthetic portrait image with facial structure for testing."""
    img = np.ones((300, 300, 3), dtype=np.uint8) * 240
    
    # Head oval
    cv2.ellipse(img, (150, 150), (80, 105), 0, 0, 360, skin_tone, -1)
    cv2.ellipse(img, (150, 150), (80, 105), 0, 0, 360, (100, 80, 60), 2)
    
    # Eyes
    cv2.circle(img, (120 + eye_offset, 130), 10, (255, 255, 255), -1)
    cv2.circle(img, (180 + eye_offset, 130), 10, (255, 255, 255), -1)
    cv2.circle(img, (120 + eye_offset, 130), 5, (40, 25, 10), -1)
    cv2.circle(img, (180 + eye_offset, 130), 5, (40, 25, 10), -1)
    
    # Nose
    cv2.line(img, (150, 135), (150, 165), (120, 90, 70), 3)
    
    # Mouth
    if smile:
        cv2.ellipse(img, (150, 195), (25, 12), 0, 0, 180, (50, 40, 150), -1)
    else:
        cv2.line(img, (130, 200), (170, 200), (50, 40, 150), 3)
        
    # Hair
    cv2.ellipse(img, (150, 85), (85, 45), 0, 180, 360, (20, 20, 20), -1)

    _, buf = cv2.imencode('.jpg', img)
    return buf.tobytes()


def test_face_detection_and_liveness():
    print("[*] Testing Face Detection and Liveness Engine...")
    face_bytes = generate_synthetic_face_image()
    face_np = cv2.imdecode(np.frombuffer(face_bytes, np.uint8), cv2.IMREAD_COLOR)
    
    detection = detect_face(face_np)
    assert detection is not None, "Failed to detect face on test portrait"
    print(f" [✓] Face detected via: {detection['detector']} (Confidence: {detection['confidence']}%)")

    liveness = compute_passive_liveness(face_np, detection["crop"])
    assert liveness is not None
    assert "liveness_score" in liveness
    print(f" [✓] Passive Liveness evaluated: Score {liveness['liveness_score']}/100 ({liveness['liveness_status']})")


def test_1to1_matching():
    print("\n[*] Testing 1:1 Biometric Matching...")
    face1_bytes = generate_synthetic_face_image(skin_tone=(210, 160, 130), eye_offset=0, smile=True)
    # Same person with slight lighting/smile change
    face1_variant_bytes = generate_synthetic_face_image(skin_tone=(215, 165, 135), eye_offset=0, smile=False)
    # Different person with different features
    face2_impersonator_bytes = generate_synthetic_face_image(skin_tone=(140, 100, 70), eye_offset=15, smile=False)

    # Match 1: Same person
    match_res = match_faces_1to1(face1_bytes, face1_variant_bytes)
    assert match_res["success"] is True
    print(f" [✓] Same-person match tested: Score = {match_res['match_score']}%, Verdict = {match_res['verdict']}")

    # Match 2: Impersonation / Mismatched pair
    diff_res = match_faces_1to1(face1_bytes, face2_impersonator_bytes)
    assert diff_res["success"] is True
    print(f" [✓] Impersonation test: Score = {diff_res['match_score']}%, Verdict = {diff_res['verdict']}")


def test_fastapi_match_endpoint():
    print("\n[*] Testing FastAPI POST /match-face Endpoint...")
    doc_bytes = generate_synthetic_face_image()
    live_bytes = generate_synthetic_face_image()

    response = client.post(
        "/match-face",
        files={
            "document_image": ("doc.jpg", doc_bytes, "image/jpeg"),
            "live_face_image": ("live.jpg", live_bytes, "image/jpeg")
        }
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert "match_score" in data
    assert "liveness_score" in data
    assert data["doc_face_crop_base64"] is not None
    assert data["live_face_crop_base64"] is not None
    print(f" [✓] /match-face endpoint returned 200 OK:")
    print(f"     Verdict: {data['verdict']}")
    print(f"     Match Score: {data['match_score']}%")
    print(f"     Liveness: {data['liveness_status']} ({data['liveness_score']}/100)")
    print(f"     Doc Face Crop: {data['doc_face_crop_base64'][:40]}...")
    print(f"     Live Face Crop: {data['live_face_crop_base64'][:40]}...")


if __name__ == "__main__":
    test_face_detection_and_liveness()
    test_1to1_matching()
    test_fastapi_match_endpoint()
    print("\n[ALL BIOMETRIC TESTS PASSED SUCCESSFULLY!]")
