"""
Pydantic Data Models for API Requests and Responses
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ExtractedFieldItem(BaseModel):
    field_name: str
    value: Optional[str] = None
    status: str = Field(..., description="verified | flagged | warning")
    confidence: int = Field(..., description="Confidence score 0-100")
    anomaly_details: Optional[str] = None


class ChecksumResult(BaseModel):
    algorithm: str
    passed: bool
    details: str
    raw_extracted: Optional[str] = None
    error: Optional[str] = None


class CrossCheckResult(BaseModel):
    passed: bool
    status: str = Field(..., description="ACTIVE | NOT_FOUND | REVOKED")
    name_matched: Optional[bool] = None
    source: str = Field(..., description="supabase | in-memory-mock")
    db_record: Optional[Dict[str, Any]] = None


class ValidationCheckItem(BaseModel):
    id: str
    name: str
    category: str
    status: str = Field(..., description="pass | fail | warning")
    details: str
    score: int


class QrVerificationResult(BaseModel):
    detected: bool
    status: str = Field(..., description="VERIFIED | TAMPERED | SKIPPED")
    details: str
    raw_payload_preview: Optional[str] = None
    extracted_qr_data: Optional[Dict[str, Any]] = None


class BiometricVerificationResult(BaseModel):
    is_match: bool
    match_score: int = Field(..., ge=0, le=100, description="Biometric Match Confidence 0-100")
    cosine_similarity: float
    l2_distance: Optional[float] = None
    liveness_score: int = Field(..., ge=0, le=100)
    liveness_status: str = Field(..., description="GENUINE_LIVE_PERSON | SUSPICIOUS_PRESENTATION | SPOOF_ATTACK_DETECTED | SKIPPED")
    is_live_person: bool
    verdict: str = Field(..., description="MATCH_VERIFIED | IMPERSONATION_DETECTED | LIVENESS_FAILED | NO_FACE_DETECTED")
    verdict_description: str
    doc_face_crop_base64: Optional[str] = None
    live_face_crop_base64: Optional[str] = None
    doc_face_confidence: Optional[float] = None
    live_face_confidence: Optional[float] = None


class BiometricMatchResponse(BaseModel):
    success: bool
    verdict: str
    is_match: bool
    match_score: int
    cosine_similarity: float
    l2_distance: Optional[float] = None
    liveness_score: int
    liveness_status: str
    is_live_person: bool
    verdict_description: str
    doc_face_crop_base64: Optional[str] = None
    live_face_crop_base64: Optional[str] = None
    doc_face_confidence: Optional[float] = None
    live_face_confidence: Optional[float] = None
    forensic_trace: List[str]
    processing_time_ms: float


class ExtractAndValidateResponse(BaseModel):
    success: bool
    document_type: str
    verdict: str = Field(..., description="AUTHENTIC | SUSPICIOUS | TAMPERED")
    authenticity_score: int = Field(..., ge=0, le=100)
    confidence: float
    processing_time_ms: float
    checksum_result: ChecksumResult
    cross_check_result: CrossCheckResult
    qr_verification: Optional[QrVerificationResult] = None
    biometric_verification: Optional[BiometricVerificationResult] = None
    extracted_fields: List[ExtractedFieldItem]
    validation_checks: List[ValidationCheckItem]
    forensic_trace: List[str]
    raw_ocr_text: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None
