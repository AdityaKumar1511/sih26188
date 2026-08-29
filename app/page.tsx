'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  UploadCloud,
  FileText,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Eye,
  EyeOff,
  Scan,
  Cpu,
  Building2,
  ChevronRight,
  Download,
  Check,
  X
} from 'lucide-react';

// ============================================================================
// TYPES & DATA STRUCTURES
// ============================================================================

type AppState = 'upload' | 'processing' | 'results';

interface BoundingBox {
  id: string;
  label: string;
  type: 'critical' | 'warning' | 'info';
  x: number;
  y: number;
  width: number;
  height: number;
  description: string;
  confidence: number;
}

interface ExtractedField {
  fieldName: string;
  value: string;
  status: 'verified' | 'flagged' | 'warning';
  confidence: number;
  anomalyDetails?: string;
}

interface ValidationCheck {
  id: string;
  name: string;
  category: 'Structural' | 'Algorithmic' | 'Forensic' | 'Typography' | 'Biometric';
  status: 'pass' | 'fail' | 'warning';
  details: string;
  score: number;
}

interface ScreeningResult {
  authenticityScore: number;
  verdict: 'AUTHENTIC' | 'SUSPICIOUS' | 'TAMPERED';
  verdictDescription: string;
  processingTimeMs: number;
  documentType: string;
  confidence: number;
  boundingBoxes: BoundingBox[];
  extractedFields: ExtractedField[];
  validationChecks: ValidationCheck[];
  forensicTrace: string[];
}

interface SamplePreset {
  id: string;
  name: string;
  docType: string;
  description: string;
  badgeText: string;
  badgeStyle: 'success' | 'danger';
  previewUrl: string;
  mockResult: ScreeningResult;
}

// ============================================================================
// SAMPLE PRESET DATA (BLACK & ORANGE THEME)
// ============================================================================

const SAMPLE_PRESETS: SamplePreset[] = [
  {
    id: 'aadhaar-legit',
    name: 'Sample 1: Legitimate Aadhaar',
    docType: 'Aadhaar Card',
    description: 'Clean document with valid QR signature, matching typography, and verified checksum.',
    badgeText: 'Authentic (96%)',
    badgeStyle: 'success',
    previewUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80',
    mockResult: {
      authenticityScore: 96,
      verdict: 'AUTHENTIC',
      verdictDescription: 'Verified Authentic. Cryptographic checksums, font pitch, and micro-print structures match standard UIDAI templates.',
      processingTimeMs: 1840,
      documentType: 'Aadhaar Card (UIDAI Standard)',
      confidence: 0.98,
      boundingBoxes: [
        {
          id: 'b1',
          label: 'UIDAI Emblem & Seal',
          type: 'info',
          x: 10,
          y: 12,
          width: 20,
          height: 18,
          description: 'Official emblem alignment and micro-text pattern verified.',
          confidence: 0.99
        },
        {
          id: 'b2',
          label: 'Signed QR Code Payload',
          type: 'info',
          x: 70,
          y: 50,
          width: 22,
          height: 38,
          description: '2048-bit digital signature matches UIDAI PKI registry.',
          confidence: 0.97
        }
      ],
      extractedFields: [
        { fieldName: 'Full Name', value: 'RAJESH KUMAR SHARMA', status: 'verified', confidence: 99 },
        { fieldName: 'Aadhaar Number', value: '5489 2104 9812', status: 'verified', confidence: 98 },
        { fieldName: 'Date of Birth', value: '14/08/1988', status: 'verified', confidence: 97 },
        { fieldName: 'Gender', value: 'MALE', status: 'verified', confidence: 99 },
        { fieldName: 'Address', value: 'H-42, Sector 62, Noida, Uttar Pradesh 201301', status: 'verified', confidence: 95 }
      ],
      validationChecks: [
        { id: 'c1', name: 'Format & Layout Alignment', category: 'Structural', status: 'pass', details: 'Template dimensions match standard UIDAI spec v3.2', score: 98 },
        { id: 'c2', name: 'Verhoeff Checksum Algorithm', category: 'Algorithmic', status: 'pass', details: 'Aadhaar 12-digit Verhoeff checksum valid', score: 100 },
        { id: 'c3', name: 'Error Level Analysis (ELA)', category: 'Forensic', status: 'pass', details: 'Uniform JPEG compression map across document canvas', score: 95 },
        { id: 'c4', name: 'Typography & Microprint', category: 'Typography', status: 'pass', details: 'Font pitch, kerning, and line spacing consistent', score: 94 },
        { id: 'c5', name: 'Facial Boundary Integrity', category: 'Biometric', status: 'pass', details: 'No edge seam artifacts detected around photo frame', score: 96 }
      ],
      forensicTrace: [
        'Digital signature hash verified against public key repository.',
        'No pixel manipulation detected around Date of Birth field.',
        'Uniform noise distribution confirmed across background substrate.'
      ]
    }
  },
  {
    id: 'pan-tampered',
    name: 'Sample 2: Tampered PAN Card',
    docType: 'PAN Card',
    description: 'Modified Date of Birth font and photo replacement detected by ELA scan.',
    badgeText: 'Tampered (34%)',
    badgeStyle: 'danger',
    previewUrl: 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=800&q=80',
    mockResult: {
      authenticityScore: 34,
      verdict: 'TAMPERED',
      verdictDescription: 'Tampering Detected. Image splicing found in Date of Birth and Photo regions.',
      processingTimeMs: 2210,
      documentType: 'Permanent Account Number (PAN)',
      confidence: 0.94,
      boundingBoxes: [
        {
          id: 'b1',
          label: 'Altered Date of Birth',
          type: 'critical',
          x: 32,
          y: 46,
          width: 36,
          height: 14,
          description: 'Font family mismatch. Inconsistent pixel noise compression (ELA spike).',
          confidence: 0.96
        },
        {
          id: 'b2',
          label: 'Photo Boundary Splice',
          type: 'critical',
          x: 12,
          y: 35,
          width: 24,
          height: 38,
          description: 'Edge dissimilarity index > 0.42. Photo pasted over original card background.',
          confidence: 0.91
        }
      ],
      extractedFields: [
        { fieldName: 'Full Name', value: 'VIKRAM SINGH MEHTA', status: 'verified', confidence: 96 },
        { fieldName: 'PAN Number', value: 'ABCDE1234F', status: 'verified', confidence: 95 },
        { fieldName: 'Father\'s Name', value: 'HARISH CHANDRA MEHTA', status: 'verified', confidence: 93 },
        { fieldName: 'Date of Birth', value: '01/01/1995', status: 'flagged', confidence: 42, anomalyDetails: 'Font mismatch. Original scan raster: 12/05/1982' },
        { fieldName: 'Issue Status', value: 'Active in NSDL Registry', status: 'warning', confidence: 88 }
      ],
      validationChecks: [
        { id: 'c1', name: 'Format & Layout Alignment', category: 'Structural', status: 'pass', details: 'Card dimensions match 85.6mm x 53.98mm CR80 spec', score: 90 },
        { id: 'c2', name: 'PAN Modulo-26 Check Digit', category: 'Algorithmic', status: 'pass', details: '5th character "E" matches surname letter correctly', score: 98 },
        { id: 'c3', name: 'Error Level Analysis (ELA)', category: 'Forensic', status: 'fail', details: 'Severe ELA compression variance around Date of Birth text block', score: 18 },
        { id: 'c4', name: 'Typography & Font Consistency', category: 'Typography', status: 'fail', details: 'DOB font renders Arial instead of Income Tax OCR-B font', score: 25 },
        { id: 'c5', name: 'Facial Boundary Integrity', category: 'Biometric', status: 'fail', details: 'Color gradient discontinuity around photo margin', score: 32 }
      ],
      forensicTrace: [
        'CRITICAL: Digital patch detected on Date of Birth digits.',
        'Headshot replacement detected using Laplacian edge analysis.',
        'Card background pattern broken around photo frame.'
      ]
    }
  },
  {
    id: 'dl-fake',
    name: 'Sample 3: Fake Driving License',
    docType: 'Driving License',
    description: 'Forged document number format & non-existent QR payload.',
    badgeText: 'Fraudulent (18%)',
    badgeStyle: 'danger',
    previewUrl: 'https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=800&q=80',
    mockResult: {
      authenticityScore: 18,
      verdict: 'TAMPERED',
      verdictDescription: 'Severe Forgery. Invalid RTO series code and forged QR payload structure.',
      processingTimeMs: 2450,
      documentType: 'Indian Driving License (State Transport)',
      confidence: 0.97,
      boundingBoxes: [
        {
          id: 'b1',
          label: 'Invalid DL Number Format',
          type: 'critical',
          x: 18,
          y: 20,
          width: 55,
          height: 15,
          description: 'DL number structure fails Ministry of Road Transport algorithm.',
          confidence: 0.99
        },
        {
          id: 'b2',
          label: 'Unverified QR Payload',
          type: 'critical',
          x: 72,
          y: 55,
          width: 22,
          height: 35,
          description: 'QR code decodes to generic web link instead of signed Vahan XML payload.',
          confidence: 0.98
        }
      ],
      extractedFields: [
        { fieldName: 'Full Name', value: 'AMIT PRAKASH', status: 'flagged', confidence: 55 },
        { fieldName: 'DL Number', value: 'DL-0420210099999', status: 'flagged', confidence: 20, anomalyDetails: 'State RTO Code 0420 is non-existent' },
        { fieldName: 'Date of Issue', value: '15/03/2021', status: 'warning', confidence: 70 },
        { fieldName: 'Valid Till', value: '14/03/2041', status: 'warning', confidence: 68 },
        { fieldName: 'Blood Group', value: 'O+VE', status: 'verified', confidence: 90 }
      ],
      validationChecks: [
        { id: 'c1', name: 'Format & Layout Alignment', category: 'Structural', status: 'fail', details: 'RTO emblem alignment shifted by 4.2mm', score: 45 },
        { id: 'c2', name: 'Parivahan Checksum Algorithm', category: 'Algorithmic', status: 'fail', details: 'RTO series code 0420 does not exist in Delhi RTO database', score: 0 },
        { id: 'c3', name: 'Error Level Analysis (ELA)', category: 'Forensic', status: 'fail', details: 'Entire card canvas generated via digital graphics editor', score: 22 },
        { id: 'c4', name: 'Typography & Font Consistency', category: 'Typography', status: 'fail', details: 'Multiple font families detected across single line', score: 15 },
        { id: 'c5', name: 'Facial Boundary Integrity', category: 'Biometric', status: 'fail', details: 'Synthetic GAN-generated face detected with 89% probability', score: 11 }
      ],
      forensicTrace: [
        'CRITICAL: Non-standard RTO series code detected.',
        'QR Code payload signature mismatch (Not signed by MoRTH authority).',
        'Facial portrait exhibits deepfake GAN artifacts.'
      ]
    }
  }
];

// ============================================================================
// LIVE FASTAPI BACKEND INTEGRATION & PDF EXPORT
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://sih26188-u5f9.onrender.com';

async function analyzeDocument(fileInput: File | SamplePreset): Promise<ScreeningResult> {
  // If user selected one of the instant demo presets
  if (typeof fileInput === 'object' && 'mockResult' in fileInput) {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    return fileInput.mockResult;
  }

  // Live File Upload -> Send to FastAPI Backend
  const formData = new FormData();
  formData.append('file', fileInput as File);

  try {
    const response = await fetch(`${API_BASE_URL}/extract-and-validate`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Screening API error');
    }

    const data = await response.json();

    // Map FastAPI structured JSON to Frontend ScreeningResult
    return {
      authenticityScore: data.authenticity_score,
      verdict: data.verdict,
      verdictDescription: `${data.verdict === 'AUTHENTIC' ? 'Verified Authentic' : (data.verdict === 'TAMPERED' ? 'Tampering / Forgery Detected' : 'Suspicious / Unverified Identity')}. ${data.checksum_result.details}`,
      processingTimeMs: data.processing_time_ms,
      documentType: data.document_type,
      confidence: data.confidence,
      boundingBoxes: [
        {
          id: 'b1',
          label: data.checksum_result.passed ? 'Verified Checksum' : 'Checksum Anomaly',
          type: data.checksum_result.passed ? 'info' : 'critical',
          x: 25,
          y: 42,
          width: 50,
          height: 18,
          description: data.checksum_result.details,
          confidence: data.confidence
        },
        ...(data.qr_verification?.detected ? [{
          id: 'b2',
          label: data.qr_verification.status === 'VERIFIED' ? 'Verified QR Code' : 'Flagged QR Payload',
          type: (data.qr_verification.status === 'VERIFIED' ? 'info' : 'critical') as 'info' | 'critical',
          x: 70,
          y: 55,
          width: 25,
          height: 35,
          description: data.qr_verification.details,
          confidence: 0.95
        }] : [])
      ],
      extractedFields: data.extracted_fields.map((f: any) => ({
        fieldName: f.field_name,
        value: f.value || 'N/A',
        status: f.status,
        confidence: f.confidence,
        anomalyDetails: f.anomaly_details
      })),
      validationChecks: data.validation_checks.map((c: any) => ({
        id: c.id,
        name: c.name,
        category: c.category,
        status: c.status,
        details: c.details,
        score: c.score
      })),
      forensicTrace: data.forensic_trace
    };
  } catch (error: any) {
    console.error('Backend connection failed:', error);
    throw new Error(error.message || 'Could not connect to FastAPI screening engine at ' + API_BASE_URL);
  }
}

async function exportPdfAuditReport(screeningResult: ScreeningResult) {
  try {
    const payload = {
      document_type: screeningResult.documentType,
      verdict: screeningResult.verdict,
      authenticity_score: screeningResult.authenticityScore,
      extracted_fields: screeningResult.extractedFields.map(f => ({
        field_name: f.fieldName,
        value: f.value,
        status: f.status,
        confidence: f.confidence
      })),
      validation_checks: screeningResult.validationChecks.map(c => ({
        name: c.name,
        category: c.category,
        status: c.status,
        details: c.details,
        score: c.score
      })),
      forensic_trace: screeningResult.forensicTrace
    };

    const response = await fetch(`${API_BASE_URL}/generate-audit-report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error('Failed to generate PDF report from server');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `MHA_Forensic_Audit_${screeningResult.documentType.replace(/\s+/g, '_')}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (err: any) {
    alert(`Could not export PDF: ${err.message}`);
  }
}

// ============================================================================
// MAIN COMPONENT (BLACK & ORANGE THEME)
// ============================================================================

export default function DocumentScreeningApp() {
  const [appState, setAppState] = useState<AppState>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<SamplePreset | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  
  // Processing state
  const [processingProgress, setProcessingProgress] = useState(0);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  
  // Results state
  const [screeningResult, setScreeningResult] = useState<ScreeningResult | null>(null);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'fields' | 'checks' | 'forensics'>('fields');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processingSteps = [
    'Initializing Image Preprocessing & De-noising...',
    'Extracting OCR Text Fields & Layout Coordinates...',
    'Executing Digital Error Level Analysis (ELA)...',
    'Verifying Government Checksum & Hash Algorithms...',
    'Evaluating Facial Biometrics & Typography Alignment...'
  ];

  useEffect(() => {
    return () => {
      if (imagePreviewUrl && imagePreviewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(imagePreviewUrl);
      }
    };
  }, [imagePreviewUrl]);

  const handleFileChange = (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Please upload a valid image file (JPG or PNG).');
      return;
    }
    setSelectedFile(file);
    setSelectedPreset(null);
    setImagePreviewUrl(URL.createObjectURL(file));
  };

  const handlePresetSelect = (preset: SamplePreset) => {
    setSelectedPreset(preset);
    setSelectedFile(null);
    setImagePreviewUrl(preset.previewUrl);
  };

  const handleStartScreening = async () => {
    if (!selectedFile && !selectedPreset) return;

    setAppState('processing');
    setProcessingProgress(10);
    setCurrentStepIndex(0);

    const interval = setInterval(() => {
      setProcessingProgress((prev) => {
        if (prev >= 92) {
          clearInterval(interval);
          return 92;
        }
        const next = prev + Math.floor(Math.random() * 18) + 8;
        return next > 92 ? 92 : next;
      });
    }, 350);

    const stepInterval = setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev < processingSteps.length - 1) return prev + 1;
        clearInterval(stepInterval);
        return prev;
      });
    }, 450);

    try {
      const input = selectedPreset || selectedFile!;
      const result = await analyzeDocument(input);
      
      clearInterval(interval);
      clearInterval(stepInterval);
      setProcessingProgress(100);
      
      setTimeout(() => {
        setScreeningResult(result);
        setAppState('results');
      }, 400);
    } catch (err: any) {
      clearInterval(interval);
      clearInterval(stepInterval);
      alert(`Error analyzing document: ${err.message || 'Server connection failed'}`);
      setAppState('upload');
    }
  };

  const handleReset = () => {
    setAppState('upload');
    setSelectedFile(null);
    setSelectedPreset(null);
    setImagePreviewUrl(null);
    setScreeningResult(null);
    setSelectedBoxId(null);
    setProcessingProgress(0);
  };

  return (
    <div className="min-h-screen bg-dark-950 text-neutral-100 flex flex-col font-sans selection:bg-orange-600 selection:text-white">
      
      {/* ==================================================================== */}
      {/* TOP HEADER / BAR (BLACK & ORANGE)                                    */}
      {/* ==================================================================== */}
      <header className="border-b border-dark-700 bg-dark-900 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          
          {/* Left Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-orange-600 flex items-center justify-center text-white font-bold text-base shadow-sm">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-orange-400 bg-dark-850 px-2 py-0.5 rounded border border-orange-900/60">
                  Ministry of Home Affairs
                </span>
                <span className="text-xs text-neutral-400 font-mono">PS26188</span>
              </div>
              <h1 className="text-sm sm:text-base font-bold text-white tracking-tight">
                AI Fake Identity & Document Screening System
              </h1>
            </div>
          </div>

          {/* Right Status */}
          <div className="hidden sm:flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-dark-850 border border-dark-700 text-xs font-mono text-neutral-300">
              <span className="w-2 h-2 rounded-full bg-orange-500"></span>
              <span>ENGINE: READY</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-dark-850 border border-dark-700 text-xs font-mono text-orange-400">
              <Cpu className="w-3.5 h-3.5" />
              <span>v4.2-Forensic</span>
            </div>
          </div>

        </div>
      </header>

      {/* ==================================================================== */}
      {/* MAIN CONTAINER (BLACK & ORANGE)                                      */}
      {/* ==================================================================== */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col">
        
        {/* STATE 1: UPLOAD SCREEN */}
        {appState === 'upload' && (
          <div className="space-y-8 my-auto py-4">
            
            {/* Heading */}
            <div className="text-center max-w-2xl mx-auto space-y-2">
              <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                Verify Document Authenticity
              </h2>
              <p className="text-neutral-400 text-sm sm:text-base">
                Upload identity credentials (Aadhaar, PAN, Driving License) to run automated multi-layered AI verification for tampering, font mismatch, and checksum integrity.
              </p>
            </div>

            {/* Upload Box */}
            <div className="max-w-2xl mx-auto">
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
                onDrop={(e) => {
                  e.preventDefault();
                  setIsDragging(false);
                  if (e.dataTransfer.files?.[0]) handleFileChange(e.dataTransfer.files[0]);
                }}
                onClick={() => !imagePreviewUrl && fileInputRef.current?.click()}
                className={`matte-card p-8 text-center transition cursor-pointer relative ${
                  isDragging
                    ? 'border-orange-500 bg-dark-800'
                    : imagePreviewUrl
                    ? 'border-dark-700 bg-dark-850 cursor-default'
                    : 'border-dark-700 hover:border-orange-500/80 bg-dark-850'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/jpg"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
                />

                {!imagePreviewUrl ? (
                  <div className="space-y-4 py-4">
                    <div className="w-14 h-14 rounded-xl bg-dark-800 border border-dark-700 flex items-center justify-center mx-auto text-orange-500">
                      <UploadCloud className="w-7 h-7" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">
                        Drag and drop your document image here
                      </p>
                      <p className="text-xs text-neutral-400 mt-1 font-mono">
                        Supports JPG, JPEG, PNG up to 15MB
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        fileInputRef.current?.click();
                      }}
                      className="px-4 py-2 rounded-lg bg-dark-800 hover:bg-dark-700 text-neutral-200 text-xs font-semibold border border-dark-700 transition"
                    >
                      Browse File
                    </button>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="relative max-h-64 rounded-lg overflow-hidden border border-dark-700 bg-black flex items-center justify-center p-2">
                      {/* eslint-disable-next-html-next-image */}
                      <img
                        src={imagePreviewUrl}
                        alt="Document Preview"
                        className="max-h-60 object-contain rounded"
                      />
                      <div className="absolute top-3 right-3 bg-dark-900 px-2.5 py-1 rounded text-xs font-mono text-orange-400 border border-dark-700">
                        Selected File
                      </div>
                    </div>

                    {selectedFile && (
                      <div className="flex items-center justify-between text-xs text-neutral-300 bg-black p-3 rounded-lg border border-dark-700 font-mono">
                        <div className="flex items-center gap-2 truncate">
                          <FileText className="w-4 h-4 text-orange-500 flex-shrink-0" />
                          <span className="truncate text-white">{selectedFile.name}</span>
                        </div>
                        <span className="text-neutral-400 flex-shrink-0 ml-2">
                          {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                        </span>
                      </div>
                    )}

                    <div className="flex items-center justify-center gap-3 pt-2">
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleReset(); }}
                        className="px-4 py-2.5 rounded-lg bg-dark-800 hover:bg-dark-700 text-neutral-300 text-xs font-semibold border border-dark-700 transition"
                      >
                        Change File
                      </button>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleStartScreening(); }}
                        className="px-6 py-2.5 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs shadow-none transition flex items-center gap-2"
                      >
                        <Scan className="w-4 h-4" />
                        <span>Start Screening</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Test Sample Presets */}
            <div className="max-w-3xl mx-auto pt-2">
              <div className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-3 text-center">
                Or select a test document preset for instant demo:
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {SAMPLE_PRESETS.map((preset) => {
                  const isSelected = selectedPreset?.id === preset.id;
                  return (
                    <div
                      key={preset.id}
                      onClick={() => handlePresetSelect(preset)}
                      className={`matte-card p-4 transition cursor-pointer text-left flex flex-col justify-between ${
                        isSelected
                          ? 'border-orange-500 bg-dark-800 ring-1 ring-orange-500'
                          : 'hover:border-dark-600 bg-dark-850'
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="text-xs font-bold text-white truncate">
                            {preset.docType}
                          </span>
                          <span
                            className={`text-[10px] font-bold font-mono px-2 py-0.5 rounded ${
                              preset.badgeStyle === 'success'
                                ? 'bg-emerald-950 text-emerald-400 border border-emerald-900'
                                : 'bg-red-950 text-red-400 border border-red-900'
                            }`}
                          >
                            {preset.badgeText}
                          </span>
                        </div>
                        <p className="text-xs text-neutral-400 line-clamp-2 mb-3">
                          {preset.description}
                        </p>
                      </div>

                      <div className="pt-2 border-t border-dark-700 flex items-center justify-between text-xs text-orange-500 font-medium">
                        <span>Load Sample</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        )}

        {/* STATE 2: PROCESSING SCREEN */}
        {appState === 'processing' && (
          <div className="my-auto py-12 max-w-lg mx-auto w-full space-y-6 text-center">
            
            <div className="relative max-w-sm mx-auto aspect-[1.6/1] rounded-xl overflow-hidden border border-dark-700 bg-black">
              {imagePreviewUrl && (
                /* eslint-disable-next-html-next-image */
                <img
                  src={imagePreviewUrl}
                  alt="Scanning Target"
                  className="w-full h-full object-cover opacity-60"
                />
              )}
              {/* Clean matte orange scanning bar */}
              <div className="absolute left-0 right-0 h-1 bg-orange-500 animate-scan-laser" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-orange-400 font-semibold flex items-center gap-2">
                  <Cpu className="w-4 h-4 animate-spin text-orange-500" />
                  ANALYZING DOCUMENT STRUCTURE...
                </span>
                <span className="text-white font-bold">{processingProgress}%</span>
              </div>

              <div className="w-full h-2 bg-black rounded-full overflow-hidden border border-dark-700">
                <div
                  className="h-full bg-orange-600 transition-all duration-300 rounded-full"
                  style={{ width: `${processingProgress}%` }}
                />
              </div>
            </div>

            {/* Console Log */}
            <div className="bg-black border border-dark-700 rounded-xl p-4 text-left font-mono text-xs space-y-2">
              <div className="text-[10px] text-neutral-500 uppercase tracking-wider border-b border-dark-700 pb-1 mb-2">
                Execution Telemetry:
              </div>
              {processingSteps.map((step, idx) => {
                const isCompleted = idx < currentStepIndex;
                const isCurrent = idx === currentStepIndex;
                return (
                  <div
                    key={idx}
                    className={`flex items-center gap-2 ${
                      isCompleted
                        ? 'text-emerald-400'
                        : isCurrent
                        ? 'text-orange-400 font-semibold'
                        : 'text-neutral-600'
                    }`}
                  >
                    {isCompleted ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    ) : isCurrent ? (
                      <span className="w-3 h-3 rounded-full border-2 border-orange-500 border-t-transparent animate-spin flex-shrink-0" />
                    ) : (
                      <span className="w-3 h-3 rounded-full border border-dark-700 flex-shrink-0" />
                    )}
                    <span className="truncate">{step}</span>
                  </div>
                );
              })}
            </div>

          </div>
        )}

        {/* STATE 3: RESULTS SCREEN */}
        {appState === 'results' && screeningResult && (
          <div className="space-y-6">
            
            {/* Top Score Banner */}
            <div className="matte-card p-6 border border-dark-700 flex flex-col md:flex-row items-center justify-between gap-6">
              
              <div className="flex items-center gap-6">
                
                {/* Score Box */}
                <div className={`w-20 h-20 rounded-xl flex flex-col items-center justify-center font-mono border ${
                  screeningResult.verdict === 'AUTHENTIC'
                    ? 'bg-emerald-950/80 border-emerald-800 text-emerald-400'
                    : screeningResult.verdict === 'SUSPICIOUS'
                    ? 'bg-amber-950/70 border-amber-800/80 text-amber-400'
                    : 'bg-red-950/80 border-red-900 text-red-400'
                }`}>
                  <span className="text-2xl font-extrabold">{screeningResult.authenticityScore}</span>
                  <span className="text-[10px] text-neutral-400 font-sans uppercase">Score</span>
                </div>

                {/* Verdict Info */}
                <div className="space-y-1 text-left">
                  <div className="flex items-center gap-3">
                    <span className={`text-xs font-bold font-mono px-2.5 py-1 rounded border ${
                      screeningResult.verdict === 'AUTHENTIC'
                        ? 'bg-emerald-950 text-emerald-400 border-emerald-900'
                        : screeningResult.verdict === 'SUSPICIOUS'
                        ? 'bg-amber-950 text-amber-400 border-amber-900/80'
                        : 'bg-red-950 text-red-400 border-red-900'
                    }`}>
                      {screeningResult.verdict === 'AUTHENTIC'
                        ? '✓ VERIFIED AUTHENTIC'
                        : screeningResult.verdict === 'SUSPICIOUS'
                        ? '⚠ SUSPICIOUS / UNVERIFIED'
                        : '✕ TAMPERING DETECTED'}
                    </span>
                    <span className="text-xs text-neutral-400 font-mono">
                      Type: <strong className="text-white">{screeningResult.documentType}</strong>
                    </span>
                  </div>
                  <h3 className="text-base sm:text-lg font-bold text-white">
                    {screeningResult.verdictDescription}
                  </h3>
                  <p className="text-xs text-neutral-400">
                    Execution time: <span className="text-neutral-200 font-mono">{screeningResult.processingTimeMs}ms</span> • Confidence: <span className="text-neutral-200 font-mono">{(screeningResult.confidence * 100).toFixed(0)}%</span>
                  </p>
                </div>

              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3 w-full md:w-auto justify-end border-t md:border-t-0 pt-4 md:pt-0 border-dark-700">
                <button
                  onClick={() => exportPdfAuditReport(screeningResult)}
                  className="px-3.5 py-2 rounded-lg bg-dark-800 hover:bg-dark-700 text-neutral-200 text-xs font-semibold border border-dark-700 flex items-center gap-2 transition cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5 text-neutral-300" />
                  <span>Export Report (PDF)</span>
                </button>

                <button
                  onClick={handleReset}
                  className="px-4 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs transition flex items-center gap-2 shadow-none cursor-pointer"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Screen Another</span>
                </button>
              </div>

            </div>

            {/* Inspector Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              {/* Left Column: Bounding Box Inspector */}
              <div className="lg:col-span-7 matte-card p-5 border border-dark-700 space-y-4 flex flex-col">
                
                <div className="flex items-center justify-between text-xs border-b border-dark-700 pb-3">
                  <div className="flex items-center gap-2 font-bold text-white">
                    <Scan className="w-4 h-4 text-orange-500" />
                    <span>Document Canvas & Flagged Regions</span>
                  </div>
                  <button
                    onClick={() => setShowBoundingBoxes(!showBoundingBoxes)}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded border text-xs font-mono transition ${
                      showBoundingBoxes
                        ? 'bg-dark-800 border-dark-700 text-white'
                        : 'bg-black border-dark-700 text-neutral-500'
                    }`}
                  >
                    {showBoundingBoxes ? <Eye className="w-3.5 h-3.5 text-orange-500" /> : <EyeOff className="w-3.5 h-3.5" />}
                    <span>Overlays ({screeningResult.boundingBoxes.length})</span>
                  </button>
                </div>

                {/* Canvas Container */}
                <div className="relative flex-1 min-h-[320px] max-h-[460px] rounded-lg overflow-hidden bg-black border border-dark-700 flex items-center justify-center p-2">
                  {imagePreviewUrl && (
                    <div className="relative inline-block max-w-full max-h-full">
                      {/* eslint-disable-next-html-next-image */}
                      <img
                        src={imagePreviewUrl}
                        alt="Document Canvas"
                        className="max-h-[420px] object-contain rounded"
                      />

                      {/* Bounding Box Overlays */}
                      {showBoundingBoxes &&
                        screeningResult.boundingBoxes.map((box) => {
                          const isSelected = selectedBoxId === box.id;
                          const isCritical = box.type === 'critical';

                          const boxStyle = isCritical
                            ? 'border-2 border-red-500 bg-red-950/40 text-red-300'
                            : 'border-2 border-orange-500 bg-orange-950/40 text-orange-300';

                          return (
                            <div
                              key={box.id}
                              onClick={() => setSelectedBoxId(box.id)}
                              style={{
                                left: `${box.x}%`,
                                top: `${box.y}%`,
                                width: `${box.width}%`,
                                height: `${box.height}%`
                              }}
                              className={`absolute rounded cursor-pointer transition ${boxStyle} ${
                                isSelected ? 'ring-2 ring-white z-30' : 'z-20'
                              }`}
                            >
                              <div className="absolute -top-6 left-0 bg-dark-900 border border-dark-700 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold whitespace-nowrap text-white">
                                {box.label}
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  )}
                </div>

                {/* Region Legend */}
                <div className="space-y-2 pt-1">
                  <span className="text-[11px] font-bold text-neutral-400 uppercase tracking-wider">
                    Flagged Anomalies:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {screeningResult.boundingBoxes.map((box) => (
                      <div
                        key={box.id}
                        onClick={() => setSelectedBoxId(box.id)}
                        className={`p-2.5 rounded-lg border text-xs cursor-pointer transition ${
                          selectedBoxId === box.id
                            ? 'border-orange-500 bg-dark-800'
                            : 'border-dark-700 hover:border-dark-600 bg-black'
                        }`}
                      >
                        <div className="flex items-center gap-2 font-bold text-white">
                          {box.type === 'critical' ? (
                            <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                          ) : (
                            <AlertTriangle className="w-4 h-4 text-orange-500 flex-shrink-0" />
                          )}
                          <span>{box.label}</span>
                        </div>
                        <p className="text-[11px] text-neutral-400 mt-1">
                          {box.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

              </div>

              {/* Right Column: Metadata & Checks */}
              <div className="lg:col-span-5 matte-card p-5 border border-dark-700 space-y-4 flex flex-col">
                
                {/* Tabs */}
                <div className="flex border-b border-dark-700 text-xs font-semibold">
                  <button
                    onClick={() => setActiveTab('fields')}
                    className={`pb-2.5 px-3 border-b-2 transition ${
                      activeTab === 'fields'
                        ? 'border-orange-500 text-orange-400'
                        : 'border-transparent text-neutral-400 hover:text-neutral-200'
                    }`}
                  >
                    Extracted Fields ({screeningResult.extractedFields.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('checks')}
                    className={`pb-2.5 px-3 border-b-2 transition ${
                      activeTab === 'checks'
                        ? 'border-orange-500 text-orange-400'
                        : 'border-transparent text-neutral-400 hover:text-neutral-200'
                    }`}
                  >
                    Validation Checks ({screeningResult.validationChecks.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('forensics')}
                    className={`pb-2.5 px-3 border-b-2 transition ${
                      activeTab === 'forensics'
                        ? 'border-orange-500 text-orange-400'
                        : 'border-transparent text-neutral-400 hover:text-neutral-200'
                    }`}
                  >
                    Forensics Trace
                  </button>
                </div>

                {/* Tab 1: Extracted Fields Table */}
                {activeTab === 'fields' && (
                  <div className="space-y-2 flex-1 overflow-y-auto max-h-[440px] pr-1">
                    <div className="border border-dark-700 rounded-lg overflow-hidden bg-black divide-y divide-dark-700">
                      {screeningResult.extractedFields.map((field, idx) => (
                        <div key={idx} className="p-3 text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-neutral-400 font-medium">{field.fieldName}</span>
                            <span
                              className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                                field.status === 'verified'
                                  ? 'bg-emerald-950 text-emerald-400 border-emerald-900'
                                  : 'bg-red-950 text-red-400 border-red-900'
                              }`}
                            >
                              {field.status.toUpperCase()} ({field.confidence}%)
                            </span>
                          </div>
                          <div className="font-mono text-white font-semibold">
                            {field.value}
                          </div>
                          {field.anomalyDetails && (
                            <div className="text-[11px] text-red-400 font-mono bg-red-950/40 p-1.5 rounded border border-red-900/60 mt-1">
                              ⚠ {field.anomalyDetails}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tab 2: Validation Checks */}
                {activeTab === 'checks' && (
                  <div className="space-y-3 flex-1 overflow-y-auto max-h-[440px] pr-1">
                    {screeningResult.validationChecks.map((check) => (
                      <div
                        key={check.id}
                        className="p-3 rounded-lg border border-dark-700 bg-black text-xs space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {check.status === 'pass' ? (
                              <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                            ) : (
                              <X className="w-4 h-4 text-red-500 flex-shrink-0" />
                            )}
                            <span className="font-bold text-white">{check.name}</span>
                          </div>
                          <span
                            className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                              check.status === 'pass'
                                ? 'bg-emerald-950 text-emerald-400 border border-emerald-900'
                                : 'bg-red-950 text-red-400 border border-red-900'
                            }`}
                          >
                            {check.score}/100
                          </span>
                        </div>
                        <p className="text-[11px] text-neutral-400 pl-6">
                          {check.details}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Tab 3: Forensics Trace */}
                {activeTab === 'forensics' && (
                  <div className="space-y-3 flex-1 overflow-y-auto max-h-[440px] pr-1">
                    <div className="p-3.5 rounded-lg bg-black border border-dark-700 text-xs space-y-2 font-mono">
                      <div className="text-neutral-400 font-bold border-b border-dark-700 pb-1 text-[11px]">
                        FORENSIC TRACE LOGS
                      </div>
                      <ul className="space-y-2">
                        {screeningResult.forensicTrace.map((item, i) => (
                          <li key={i} className="flex items-start gap-2 text-neutral-300 text-[11px]">
                            <span className="text-orange-500 font-bold">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="p-3 rounded-lg bg-black border border-dark-700 text-[11px] text-neutral-400 font-mono space-y-1">
                      <div className="text-orange-500 font-bold">FastAPI Integration:</div>
                      <p>Swap <code className="text-white">analyzeDocument(file)</code> in <code className="text-white">app/page.tsx</code> with your endpoint call.</p>
                    </div>
                  </div>
                )}

              </div>

            </div>

          </div>
        )}

      </main>

      {/* FOOTER */}
      <footer className="border-t border-dark-700 bg-dark-900 text-xs text-neutral-400 py-3">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <span>Ministry of Home Affairs (MHA) • Smart India Hackathon PS26188</span>
          </div>
          <div className="font-mono text-[11px] text-orange-400">
            Document Verification Portal
          </div>
        </div>
      </footer>
    </div>
  );
}
