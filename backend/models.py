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
    extracted_fields: List[ExtractedFieldItem]
    validation_checks: List[ValidationCheckItem]
    forensic_trace: List[str]
    raw_ocr_text: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None
