"""
FastAPI Server for AI-Based Fake Identity & Document Screening System
Smart India Hackathon (SIH PS 26188 - Ministry of Home Affairs)
"""

import time
import io
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from PIL import Image

from validators import validate_aadhaar_number, validate_pan_number, validate_passport_number, parse_mrz_td3
from ocr import perform_ocr, parse_document_fields
from db import cross_check_record
from face_matcher import match_faces_1to1
from models import (
    ExtractAndValidateResponse,
    ExtractedFieldItem,
    ChecksumResult,
    CrossCheckResult,
    ValidationCheckItem,
    BiometricVerificationResult,
    BiometricMatchResponse,
    ErrorResponse
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MHA AI Document Screening & Biometric Verification API",
    description="SIH PS 26188: Automated Identity Document Extraction, Algorithmic Validation, ELA Forensics & 1:1 Live Biometric Face Matching",
    version="1.1.0"
)

# Enable CORS for Next.js frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "AI Document Screening & Biometric API (PS26188)",
        "version": "1.1.0",
        "endpoints": ["/extract-and-validate", "/match-face", "/generate-audit-report", "/health", "/docs"]
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/match-face", response_model=BiometricMatchResponse)
@app.post("/match-face/", response_model=BiometricMatchResponse)
async def match_face_endpoint(
    document_image: UploadFile = File(..., description="Scanned Document or Passport Image"),
    live_face_image: UploadFile = File(..., description="Live Passenger Camera Snapshot")
):
    """
    Dedicated 1:1 Live Biometric Face Matching Endpoint:
    1. Ingests Document Scan and Live Passenger Camera snapshot.
    2. Detects facial bounding box and extracts passenger portrait from document.
    3. Detects face and evaluates passive anti-spoofing / liveness on live camera frame.
    4. Computes 128-D Deep Feature Embeddings via SFace & Cosine distance metric.
    5. Returns normalized face crops in Base64 for instant UI comparison and forensic verdict.
    """
    start_time = time.perf_counter()

    try:
        doc_bytes = await document_image.read()
        live_bytes = await live_face_image.read()

        if len(doc_bytes) == 0 or len(live_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or both uploaded image files are empty."
            )

        # Run 1:1 Biometric matching pipeline
        result = match_faces_1to1(doc_bytes, live_bytes)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return BiometricMatchResponse(
            success=result.get("success", False),
            verdict=result.get("verdict", "ERROR"),
            is_match=result.get("is_match", False),
            match_score=result.get("match_score", 0),
            cosine_similarity=result.get("cosine_similarity", 0.0),
            l2_distance=result.get("l2_distance"),
            liveness_score=result.get("liveness_score", 0),
            liveness_status=result.get("liveness_status", "UNKNOWN"),
            is_live_person=result.get("is_live_person", False),
            verdict_description=result.get("verdict_description", ""),
            doc_face_crop_base64=result.get("doc_face_crop_base64"),
            live_face_crop_base64=result.get("live_face_crop_base64"),
            doc_face_confidence=result.get("doc_face_confidence"),
            live_face_confidence=result.get("live_face_confidence"),
            forensic_trace=result.get("forensic_trace", []),
            processing_time_ms=elapsed_ms
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Biometric matching failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Biometric face matching processing failed: {str(e)}"
        )


@app.post("/extract-and-validate", response_model=ExtractAndValidateResponse)
@app.post("/extract-and-validate/", response_model=ExtractAndValidateResponse)
async def extract_and_validate(
    file: UploadFile = File(...),
    live_face: Optional[UploadFile] = File(None)
):
    """
    Main Screening & Verification Endpoint:
    1. Ingests uploaded image scan (Aadhaar, PAN, Passport, DL).
    2. Executes OCR with OpenCV preprocessing.
    3. Extracts structured entity fields (Name, DOB, ID Number, Gender/Father).
    4. Validates ID numbers algorithmically (Aadhaar 12-digit Verhoeff, PAN, or Passport MRZ).
    5. Runs Error Level Analysis (ELA) and Image Quality metrics.
    6. Cross-checks against the Supabase government registry.
    7. Optionally runs 1:1 Live Biometric Face Matching if passenger camera snapshot is supplied.
    8. Returns structured verdict, confidence scores, and forensic trace telemetry.
    """
    start_time = time.perf_counter()

    # 1. Validate File MIME Type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Please upload an image (JPEG/PNG)."
        )

    # 2. Read file bytes and verify image integrity
    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )
        
        img = Image.open(io.BytesIO(contents))
        img.verify()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image read error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted or unreadable image file. Please provide a valid JPG or PNG scan."
        )

    # 3. Perform OCR & Entity Parsing
    try:
        ocr_result = perform_ocr(contents)
        parsed_fields = parse_document_fields(ocr_result)
    except Exception as e:
        logger.error(f"OCR execution failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}"
        )

    doc_type = parsed_fields.get("doc_type", "UNKNOWN")
    id_number = parsed_fields.get("id_number")
    name = parsed_fields.get("name")
    dob = parsed_fields.get("dob")
    gender = parsed_fields.get("gender")
    father_name = parsed_fields.get("father_name")
    confidences = parsed_fields.get("confidence_scores", {})
    engine_used = ocr_result.get("engine_used", "none")

    forensic_trace: List[str] = [
        f"Ingested file '{file.filename}' ({len(contents) / 1024:.1f} KB).",
        f"OCR Engine: {engine_used.upper()}.",
        f"Document classified as: {doc_type}."
    ]

    # 4. Algorithmic Checksum Validation
    checksum_passed = False
    checksum_details = "No valid document identifier detected for algorithmic check."
    checksum_algo = "N/A"
    checksum_error = None

    if doc_type == "AADHAAR" and id_number:
        checksum_algo = "Verhoeff Checksum (D8 Dihedral Group)"
        v_res = validate_aadhaar_number(id_number)
        checksum_passed = v_res["checksum_passed"]
        if checksum_passed:
            checksum_details = "12-digit Aadhaar Verhoeff checksum verified successfully."
            forensic_trace.append("Verhoeff check digit passed (UIDAI spec v3.2).")
        else:
            checksum_details = v_res.get("error", "Failed Verhoeff checksum calculation.")
            checksum_error = v_res.get("error")
            forensic_trace.append(f"CRITICAL: {checksum_details}")

    elif doc_type == "PAN" and id_number:
        checksum_algo = "Income Tax Department Modulo / Syntax Rule"
        p_res = validate_pan_number(id_number, holder_name=name)
        checksum_passed = p_res["checksum_passed"]
        if checksum_passed:
            checksum_details = p_res.get("details", "Valid PAN format structure.")
            forensic_trace.append(f"PAN format valid. Entity: {p_res.get('entity_type')}.")
            if p_res.get("warning"):
                forensic_trace.append(f"WARNING: {p_res['warning']}")
        else:
            checksum_details = p_res.get("error", "Invalid PAN structure.")
            checksum_error = p_res.get("error")
            forensic_trace.append(f"CRITICAL: {checksum_details}")

    elif doc_type == "PASSPORT" and id_number:
        checksum_algo = "Passport Syntax + ICAO 9303 MRZ Check Digits"
        pp_res = validate_passport_number(id_number)
        checksum_passed = pp_res["checksum_passed"]
        if checksum_passed:
            checksum_details = pp_res.get("details", "Valid passport format.")
            forensic_trace.append(f"Passport syntax valid (Series {pp_res.get('series', '?')}).")
        else:
            checksum_details = pp_res.get("error", "Invalid passport format.")
            checksum_error = pp_res.get("error")
            forensic_trace.append(f"CRITICAL: {checksum_details}")

        mrz_result = parsed_fields.get("mrz_result")
        if mrz_result:
            if mrz_result.get("valid"):
                passed_count = sum(1 for v in mrz_result.get("check_digits", {}).values() if v.get("passed"))
                checksum_details += f" MRZ verified: {passed_count}/4 ICAO check digits passed."
                forensic_trace.append(f"MRZ ICAO 9303: All {passed_count} check digits PASSED.")
            else:
                checksum_passed = False
                failed_checks = [k for k, v in mrz_result.get("check_digits", {}).items() if not v.get("passed")]
                checksum_details += f" MRZ FAILED on: {', '.join(failed_checks)}."
                checksum_error = mrz_result.get("details", "MRZ check digit failure.")
                forensic_trace.append(f"CRITICAL: MRZ tampered — failed checks: {', '.join(failed_checks)}.")
    else:
        forensic_trace.append("WARNING: Unable to locate standard Aadhaar or PAN identifier number.")

    # 5. QR Code Detection & Cross-Verification
    from ocr import detect_and_decode_qr, cross_verify_qr
    qr_res = detect_and_decode_qr(contents)
    qr_verify = cross_verify_qr(qr_res, parsed_fields)

    if qr_res.get("qr_detected"):
        if qr_verify.get("qr_verified"):
            forensic_trace.append("QR Code verified: Demographic payload matches printed card text.")
        else:
            forensic_trace.append(f"CRITICAL: {qr_verify.get('details')}")
    else:
        forensic_trace.append("Digital QR code: Not detected or unreadable on this canvas.")

    # 6. Forensic Image Analysis (ELA & Sharpness)
    from forensics import compute_ela, compute_image_sharpness_and_lighting
    ela_res = compute_ela(contents)
    sharp_res = compute_image_sharpness_and_lighting(contents)

    if ela_res.get("is_tampered_by_ela"):
        forensic_trace.append(f"CRITICAL: Compression anomaly detected via ELA ({ela_res['details']}). Possible digital splicing.")
    else:
        forensic_trace.append(f"Error Level Analysis (ELA) clear. ({ela_res['details']}).")

    forensic_trace.append(f"Image Quality Assessment: {sharp_res['details']}.")

    # 7. Database Cross-Check (Supabase / Mock)
    db_result = await cross_check_record(
        doc_type=doc_type,
        id_number=id_number or "",
        extracted_name=name,
        extracted_dob=dob
    )

    db_passed = db_result["exists_in_db"] and db_result["status"] == "ACTIVE"
    if db_passed:
        forensic_trace.append(f"Registry match confirmed via {db_result['source']} (Status: ACTIVE).")
        if db_result.get("name_matched"):
            forensic_trace.append("Extracted name matches registered record.")
        elif db_result.get("name_matched") is False:
            forensic_trace.append("WARNING: Extracted name does not match registered name in database.")
    else:
        if db_result["status"] == "REVOKED":
            forensic_trace.append("CRITICAL: Identifier is marked as REVOKED/BLOCKED in government database.")
        else:
            forensic_trace.append(f"Registry lookup: ID not found in {db_result['source']} (Unverified record).")

    # 8. Optional Live Biometric Face Matching (if live_face is provided)
    biometric_verification_obj: Optional[BiometricVerificationResult] = None
    biometric_score = 0
    if live_face is not None:
        try:
            live_bytes = await live_face.read()
            if len(live_bytes) > 0:
                face_match_res = match_faces_1to1(contents, live_bytes)
                if face_match_res.get("success"):
                    biometric_score = face_match_res.get("match_score", 0)
                    biometric_verification_obj = BiometricVerificationResult(
                        is_match=face_match_res.get("is_match", False),
                        match_score=face_match_res.get("match_score", 0),
                        cosine_similarity=face_match_res.get("cosine_similarity", 0.0),
                        l2_distance=face_match_res.get("l2_distance"),
                        liveness_score=face_match_res.get("liveness_score", 0),
                        liveness_status=face_match_res.get("liveness_status", "UNKNOWN"),
                        is_live_person=face_match_res.get("is_live_person", False),
                        verdict=face_match_res.get("verdict", "UNKNOWN"),
                        verdict_description=face_match_res.get("verdict_description", ""),
                        doc_face_crop_base64=face_match_res.get("doc_face_crop_base64"),
                        live_face_crop_base64=face_match_res.get("live_face_crop_base64"),
                        doc_face_confidence=face_match_res.get("doc_face_confidence"),
                        live_face_confidence=face_match_res.get("live_face_confidence")
                    )
                    forensic_trace.append(f"Biometric Face Match: {face_match_res['verdict_description']}")
        except Exception as e:
            logger.warning(f"Live face verification encountered an error: {e}")

    # 9. Build Extracted Fields List
    extracted_items: List[ExtractedFieldItem] = []
    
    if name:
        extracted_items.append(ExtractedFieldItem(
            field_name="Full Name",
            value=name,
            status="verified" if (db_result.get("name_matched") is not False and db_passed) else "warning",
            confidence=confidences.get("name", 80),
            anomaly_details="Unregistered in government database" if not db_passed else ("Name mismatch with registry" if db_result.get("name_matched") is False else None)
        ))
    
    if id_number:
        extracted_items.append(ExtractedFieldItem(
            field_name=f"{doc_type} Number" if doc_type != "UNKNOWN" else "ID Number",
            value=id_number,
            status="verified" if checksum_passed else "flagged",
            confidence=confidences.get("id_number", 85),
            anomaly_details=checksum_error if not checksum_passed else None
        ))

    if dob:
        extracted_items.append(ExtractedFieldItem(
            field_name="Date of Birth",
            value=dob,
            status="verified",
            confidence=confidences.get("dob", 85)
        ))

    if gender:
        extracted_items.append(ExtractedFieldItem(
            field_name="Gender",
            value=gender,
            status="verified",
            confidence=confidences.get("gender", 90)
        ))

    if father_name:
        extracted_items.append(ExtractedFieldItem(
            field_name="Father's Name",
            value=father_name,
            status="verified",
            confidence=confidences.get("father_name", 80)
        ))

    # Passport-specific fields
    if doc_type == "PASSPORT":
        place_of_birth = parsed_fields.get("place_of_birth")
        if place_of_birth:
            extracted_items.append(ExtractedFieldItem(
                field_name="Place of Birth",
                value=place_of_birth,
                status="verified",
                confidence=confidences.get("place_of_birth", 80)
            ))

        expiry_date = parsed_fields.get("expiry_date")
        if expiry_date:
            extracted_items.append(ExtractedFieldItem(
                field_name="Date of Expiry",
                value=expiry_date,
                status="verified",
                confidence=confidences.get("expiry_date", 85)
            ))

        nationality = parsed_fields.get("nationality")
        if nationality:
            extracted_items.append(ExtractedFieldItem(
                field_name="Nationality",
                value=nationality,
                status="verified",
                confidence=confidences.get("nationality", 90)
            ))

    if not extracted_items:
        extracted_items.append(ExtractedFieldItem(
            field_name="Scan Quality",
            value="Unclear text content",
            status="flagged",
            confidence=20,
            anomaly_details="Could not parse recognized identity fields from scan."
        ))

    # 10. Compute Dynamic Validation Checks across Multi-Pillar Matrix
    validation_checks: List[ValidationCheckItem] = []

    ocr_word_confs = [item.get("conf", 0) for item in ocr_result.get("ocr_data", []) if item.get("conf", 0) > 10]
    avg_ocr_conf = int(sum(ocr_word_confs) / max(1, len(ocr_word_confs))) if ocr_word_confs else (40 if not extracted_items else 75)
    
    validation_checks.append(ValidationCheckItem(
        id="c1",
        name="Document Layout & OCR Extraction",
        category="Structural",
        status="pass" if avg_ocr_conf >= 60 and len(extracted_items) >= 2 else "fail",
        details=f"Extracted {len(extracted_items)} fields. OCR Engine Confidence: {avg_ocr_conf}%.",
        score=avg_ocr_conf
    ))

    chk_score = 100 if checksum_passed else (0 if id_number else 20)
    validation_checks.append(ValidationCheckItem(
        id="c2",
        name="Algorithmic Checksum Verification",
        category="Algorithmic",
        status="pass" if checksum_passed else "fail",
        details=checksum_details,
        score=chk_score
    ))

    qr_score = qr_verify.get("score", 70)
    validation_checks.append(ValidationCheckItem(
        id="c3",
        name="Digital QR Payload Cross-Check",
        category="Digital Forensic",
        status="pass" if qr_verify.get("qr_verified") else ("fail" if qr_verify.get("qr_status") == "TAMPERED" else "warning"),
        details=qr_verify.get("details", "QR status evaluated."),
        score=qr_score
    ))

    ela_score = ela_res.get("ela_score", 80)
    validation_checks.append(ValidationCheckItem(
        id="c4",
        name="Error Level Analysis (ELA Splicing)",
        category="Forensic",
        status="pass" if not ela_res.get("is_tampered_by_ela") else "fail",
        details=ela_res.get("details", "Compression map uniform across canvas."),
        score=ela_score
    ))

    sharp_score = sharp_res.get("sharpness_score", 75)
    validation_checks.append(ValidationCheckItem(
        id="c5",
        name="Optical Focus & Substrate Quality",
        category="Forensic",
        status="pass" if sharp_res.get("blur_level") != "BLURRY" else "warning",
        details=sharp_res.get("details", "Focus level evaluated."),
        score=sharp_score
    ))

    db_score = 100 if db_passed else (0 if db_result["status"] in ("REVOKED", "NOT_FOUND") else 50)
    validation_checks.append(ValidationCheckItem(
        id="c6",
        name="Government Registry Confirmation",
        category="Registry",
        status="pass" if db_passed else "fail",
        details=f"Source: {db_result['source']} • Status: {db_result['status']}",
        score=db_score
    ))

    # Check 7 (Biometric Check if provided)
    if biometric_verification_obj is not None:
        validation_checks.append(ValidationCheckItem(
            id="c7_bio",
            name="1:1 Live Biometric Face Verification",
            category="Biometric",
            status="pass" if biometric_verification_obj.is_match else "fail",
            details=biometric_verification_obj.verdict_description,
            score=biometric_verification_obj.match_score
        ))

    # Weighted composite Authenticity Score (0-100)
    if biometric_verification_obj is not None:
        # With Biometric: OCR 10%, Checksum 20%, QR 10%, ELA 15%, Sharpness 5%, Registry 15%, Biometrics 25%
        weights = [0.10, 0.20, 0.10, 0.15, 0.05, 0.15, 0.25]
        scores = [avg_ocr_conf, chk_score, qr_score, ela_score, sharp_score, db_score, biometric_score]
    else:
        weights = [0.15, 0.25, 0.15, 0.15, 0.10, 0.20]
        scores = [avg_ocr_conf, chk_score, qr_score, ela_score, sharp_score, db_score]

    authenticity_score = int(sum(w * s for w, s in zip(weights, scores)))

    # Verdict Logic
    if (not checksum_passed and id_number) or qr_verify.get("qr_status") == "TAMPERED":
        verdict = "TAMPERED"
        authenticity_score = min(authenticity_score, 35)
    elif db_result["status"] == "REVOKED" or ela_res.get("is_tampered_by_ela"):
        verdict = "TAMPERED"
        authenticity_score = min(authenticity_score, 35)
    elif biometric_verification_obj is not None and not biometric_verification_obj.is_match:
        verdict = "TAMPERED"
        authenticity_score = min(authenticity_score, 30)
    elif db_passed and checksum_passed and authenticity_score >= 80:
        verdict = "AUTHENTIC"
    else:
        verdict = "SUSPICIOUS"

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return ExtractAndValidateResponse(
        success=True,
        document_type=doc_type,
        verdict=verdict,
        authenticity_score=authenticity_score,
        confidence=round(authenticity_score / 100.0, 2),
        processing_time_ms=elapsed_ms,
        checksum_result=ChecksumResult(
            algorithm=checksum_algo,
            passed=checksum_passed,
            details=checksum_details,
            raw_extracted=id_number,
            error=checksum_error
        ),
        cross_check_result=CrossCheckResult(
            passed=db_passed,
            status=db_result["status"],
            name_matched=db_result.get("name_matched"),
            source=db_result["source"],
            db_record=db_result.get("db_record")
        ),
        qr_verification={
            "detected": qr_res.get("qr_detected", False),
            "status": qr_verify.get("qr_status", "SKIPPED"),
            "details": qr_verify.get("details", ""),
            "raw_payload_preview": qr_res.get("raw_payload"),
            "extracted_qr_data": qr_res.get("parsed_data")
        },
        biometric_verification=biometric_verification_obj,
        extracted_fields=extracted_items,
        validation_checks=validation_checks,
        forensic_trace=forensic_trace,
        raw_ocr_text=ocr_result.get("raw_text")
    )


@app.post("/generate-audit-report")
@app.post("/generate-audit-report/")
async def generate_audit_report_endpoint(screening_data: Dict[str, Any]):
    """
    Generates a timestamped official PDF forensic audit certificate.
    """
    try:
        from report_generator import generate_pdf_report
        pdf_bytes = generate_pdf_report(screening_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=MHA_Forensic_Audit_Report.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build PDF report: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
