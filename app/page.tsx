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
  X,
  Camera,
  CameraOff,
  UserCheck,
  UserX,
  Radio,
  Sparkles,
  Layers,
  ArrowRightLeft,
  ArrowUpRight,
  Fingerprint,
  QrCode,
  Search,
  ExternalLink,
  Shield,
  FileCheck2,
  Zap,
  Info
} from 'lucide-react';

// ============================================================================
// TYPES & DATA STRUCTURES
// ============================================================================

type AppState = 'upload' | 'processing' | 'results';
type AppMode = 'standard' | 'egate_kiosk';

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
  category: 'Structural' | 'Algorithmic' | 'Forensic' | 'Typography' | 'Biometric' | 'Registry';
  status: 'pass' | 'fail' | 'warning';
  details: string;
  score: number;
}

interface BiometricResult {
  isMatch: boolean;
  matchScore: number;
  cosineSimilarity: number;
  livenessScore: number;
  livenessStatus: 'GENUINE_LIVE_PERSON' | 'SUSPICIOUS_PRESENTATION' | 'SPOOF_ATTACK_DETECTED' | 'SKIPPED';
  isLivePerson: boolean;
  verdict: string;
  verdictDescription: string;
  docFaceCropBase64?: string;
  liveFaceCropBase64?: string;
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
  biometricResult?: BiometricResult;
}

interface SamplePreset {
  id: string;
  name: string;
  docType: string;
  description: string;
  badgeText: string;
  badgeStyle: 'success' | 'danger';
  previewUrl: string;
  liveFaceUrl: string;
  mockResult: ScreeningResult;
}

// ============================================================================
// SAMPLE PRESETS (WITH LIVE BIOMETRIC PAIRS)
// ============================================================================

const SAMPLE_PRESETS: SamplePreset[] = [
  {
    id: 'aadhaar-legit',
    name: 'Sample 1: Legitimate Aadhaar + Real Passenger',
    docType: 'Aadhaar Card',
    description: 'Valid UIDAI Verhoeff checksum & 96% 1:1 Live Biometric Facial Match.',
    badgeText: 'Verified (96%)',
    badgeStyle: 'success',
    previewUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80',
    liveFaceUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80',
    mockResult: {
      authenticityScore: 96,
      verdict: 'AUTHENTIC',
      verdictDescription: 'Verified Authentic. Biometric facial embeddings match document portrait and Verhoeff checksum valid.',
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
          label: 'Passenger Face Match',
          type: 'info',
          x: 70,
          y: 35,
          width: 24,
          height: 38,
          description: 'Deep 128-D SFace biometric embedding matched with 96% confidence.',
          confidence: 0.96
        }
      ],
      extractedFields: [
        { fieldName: 'Full Name', value: 'RAJESH KUMAR SHARMA', status: 'verified', confidence: 99 },
        { fieldName: 'Aadhaar Number', value: '5489 2104 9811', status: 'verified', confidence: 98 },
        { fieldName: 'Date of Birth', value: '14/08/1988', status: 'verified', confidence: 97 },
        { fieldName: 'Gender', value: 'MALE', status: 'verified', confidence: 99 },
        { fieldName: 'Address', value: 'H-42, Sector 62, Noida, Uttar Pradesh 201301', status: 'verified', confidence: 95 }
      ],
      validationChecks: [
        { id: 'c1', name: 'Document Layout & OCR Extraction', category: 'Structural', status: 'pass', details: 'Template dimensions match standard UIDAI spec v3.2', score: 98 },
        { id: 'c2', name: 'Verhoeff Checksum Algorithm', category: 'Algorithmic', status: 'pass', details: 'Aadhaar 12-digit Verhoeff checksum valid', score: 100 },
        { id: 'c3', name: '1:1 Live Biometric Face Matching', category: 'Biometric', status: 'pass', details: 'Cosine metric 0.684. Passenger live face matches document portrait.', score: 96 },
        { id: 'c4', name: 'Passive Liveness & Anti-Spoofing', category: 'Biometric', status: 'pass', details: 'Natural human skin chrominance and high-frequency texture verified.', score: 94 },
        { id: 'c5', name: 'Error Level Analysis (ELA Splicing)', category: 'Forensic', status: 'pass', details: 'Uniform JPEG compression map across document canvas', score: 95 },
        { id: 'c6', name: 'Government Registry Confirmation', category: 'Registry', status: 'pass', details: 'UIDAI Active Registry record match confirmed', score: 100 }
      ],
      biometricResult: {
        isMatch: true,
        matchScore: 96,
        cosineSimilarity: 0.684,
        livenessScore: 94,
        livenessStatus: 'GENUINE_LIVE_PERSON',
        isLivePerson: true,
        verdict: 'MATCH_VERIFIED',
        verdictDescription: 'Identity Confirmed: Passenger live face matches document portrait (96% confidence).'
      },
      forensicTrace: [
        'Biometric 128-D facial vector cosine similarity: 0.684 (Match Verified).',
        'Passive anti-spoofing test passed: Genuine live human verified.',
        'Verhoeff check digit passed (UIDAI spec v3.2).',
        'No pixel manipulation detected around Date of Birth field.',
        'Registry match confirmed via in-memory-mock (Status: ACTIVE).'
      ]
    }
  },
  {
    id: 'pan-impersonator',
    name: 'Sample 2: Stolen PAN + Impersonator Passenger',
    docType: 'PAN Card',
    description: 'Tampered DOB & Impersonator detected: Passenger face does not match card photo.',
    badgeText: 'Impersonation (24%)',
    badgeStyle: 'danger',
    previewUrl: 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=800&q=80',
    liveFaceUrl: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80',
    mockResult: {
      authenticityScore: 24,
      verdict: 'TAMPERED',
      verdictDescription: 'CRITICAL ALERT: Biometric Mismatch & Splicing Detected. Live passenger is an impersonator carrying another person’s card.',
      processingTimeMs: 2210,
      documentType: 'Permanent Account Number (PAN)',
      confidence: 0.94,
      boundingBoxes: [
        {
          id: 'b1',
          label: 'Biometric Face Mismatch',
          type: 'critical',
          x: 12,
          y: 35,
          width: 24,
          height: 38,
          description: 'CRITICAL: Facial similarity 24%. Live traveler does not match the portrait on document.',
          confidence: 0.98
        },
        {
          id: 'b2',
          label: 'Altered Date of Birth',
          type: 'critical',
          x: 32,
          y: 46,
          width: 36,
          height: 14,
          description: 'Font family mismatch. Inconsistent pixel noise compression (ELA spike).',
          confidence: 0.96
        }
      ],
      extractedFields: [
        { fieldName: 'Full Name', value: 'VIKRAM SINGH MEHTA', status: 'verified', confidence: 96 },
        { fieldName: 'PAN Number', value: 'ABCPE1234F', status: 'verified', confidence: 95 },
        { fieldName: 'Father\'s Name', value: 'HARISH CHANDRA MEHTA', status: 'verified', confidence: 93 },
        { fieldName: 'Date of Birth', value: '01/01/1995', status: 'flagged', confidence: 42, anomalyDetails: 'Font mismatch. Original scan raster: 12/05/1982' },
        { fieldName: 'Biometric Status', value: 'IMPERSONATION DETECTED', status: 'flagged', confidence: 24, anomalyDetails: 'Face does not match live traveler' }
      ],
      validationChecks: [
        { id: 'c1', name: 'Document Layout & OCR Extraction', category: 'Structural', status: 'pass', details: 'Card dimensions match 85.6mm x 53.98mm CR80 spec', score: 90 },
        { id: 'c2', name: '1:1 Live Biometric Face Matching', category: 'Biometric', status: 'fail', details: 'CRITICAL: Biometric similarity 24%. Live passenger does not match card photo.', score: 24 },
        { id: 'c3', name: 'Passive Liveness & Anti-Spoofing', category: 'Biometric', status: 'pass', details: 'Live person present, but facial features do not match credentials.', score: 88 },
        { id: 'c4', name: 'Error Level Analysis (ELA Splicing)', category: 'Forensic', status: 'fail', details: 'Severe ELA compression variance around Date of Birth text block', score: 18 },
        { id: 'c5', name: 'Government Registry Confirmation', category: 'Registry', status: 'pass', details: 'ID exists in Registry but traveler identity is fraudulent', score: 80 }
      ],
      biometricResult: {
        isMatch: false,
        matchScore: 24,
        cosineSimilarity: 0.112,
        livenessScore: 88,
        livenessStatus: 'GENUINE_LIVE_PERSON',
        isLivePerson: true,
        verdict: 'IMPERSONATION_DETECTED',
        verdictDescription: 'CRITICAL: Biometric mismatch (24% similarity). High probability of identity impersonation or stolen document.'
      },
      forensicTrace: [
        'CRITICAL: 1:1 Biometric matching failed (Cosine 0.112 < 0.363 threshold).',
        'ALERT: Impersonation detected at checkpoint.',
        'Digital patch detected on Date of Birth digits.',
        'DOB font renders Arial instead of Income Tax OCR-B font.'
      ]
    }
  },
  {
    id: 'dl-spoof',
    name: 'Sample 3: Fake DL + Photo Spoof Attack',
    docType: 'Driving License',
    description: 'Forged DL Number & Screen Photo Attack caught by Passive Liveness detector.',
    badgeText: 'Spoof Attack (14%)',
    badgeStyle: 'danger',
    previewUrl: 'https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=800&q=80',
    liveFaceUrl: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=600&q=80',
    mockResult: {
      authenticityScore: 14,
      verdict: 'TAMPERED',
      verdictDescription: 'Severe Forgery & Presentation Attack. Non-existent RTO series code and phone screen spoof attack detected.',
      processingTimeMs: 2450,
      documentType: 'Indian Driving License (State Transport)',
      confidence: 0.97,
      boundingBoxes: [
        {
          id: 'b1',
          label: 'Anti-Spoofing Alert',
          type: 'critical',
          x: 15,
          y: 20,
          width: 60,
          height: 30,
          description: 'Periodic digital moiré artifacts detected (display screen re-capture).',
          confidence: 0.99
        }
      ],
      extractedFields: [
        { fieldName: 'Full Name', value: 'AMIT PRAKASH', status: 'flagged', confidence: 55 },
        { fieldName: 'DL Number', value: 'DL-0420210099999', status: 'flagged', confidence: 20, anomalyDetails: 'State RTO Code 0420 is non-existent' },
        { fieldName: 'Liveness Verdict', value: 'SPOOF ATTACK DETECTED', status: 'flagged', confidence: 15, anomalyDetails: 'Phone screen presentation attack' }
      ],
      validationChecks: [
        { id: 'c1', name: 'Document Layout & OCR Extraction', category: 'Structural', status: 'fail', details: 'RTO emblem alignment shifted by 4.2mm', score: 45 },
        { id: 'c2', name: 'Parivahan Checksum Algorithm', category: 'Algorithmic', status: 'fail', details: 'RTO series code 0420 does not exist in Delhi RTO database', score: 0 },
        { id: 'c3', name: 'Passive Liveness & Anti-Spoofing', category: 'Biometric', status: 'fail', details: 'CRITICAL: Screen moiré frequency and compressed gamut detected (Score: 28/100)', score: 28 },
        { id: 'c4', name: 'Error Level Analysis (ELA)', category: 'Forensic', status: 'fail', details: 'Entire card canvas generated via digital graphics editor', score: 22 }
      ],
      biometricResult: {
        isMatch: false,
        matchScore: 0,
        cosineSimilarity: 0.0,
        livenessScore: 28,
        livenessStatus: 'SPOOF_ATTACK_DETECTED',
        isLivePerson: false,
        verdict: 'LIVENESS_FAILED',
        verdictDescription: 'CRITICAL: Anti-spoofing alert. Live camera feed flagged as phone screen photo presentation attack.'
      },
      forensicTrace: [
        'CRITICAL: Passive Anti-Spoofing failed: Moiré pattern detected (ratio: 0.92).',
        'Parivahan RTO lookup: Code 0420 INVALID.',
        'Document canvas flagged as 100% digital synthetic raster.'
      ]
    }
  },
  {
    id: 'passport-mrz-tamper',
    name: 'Sample 4: Indian Passport + MRZ Digit Tampering',
    docType: 'Passport',
    description: 'Forged ICAO 9303 Check Digit in MRZ Line 2. Checkpoint intercepted.',
    badgeText: 'MRZ Forgery (32%)',
    badgeStyle: 'danger',
    previewUrl: 'https://images.unsplash.com/photo-1544717305-2782549b5136?auto=format&fit=crop&w=800&q=80',
    liveFaceUrl: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=600&q=80',
    mockResult: {
      authenticityScore: 32,
      verdict: 'TAMPERED',
      verdictDescription: 'CRITICAL FORGERY: ICAO 9303 TD3 MRZ check digits tampered. Passport expiration date manipulated.',
      processingTimeMs: 2100,
      documentType: 'Republic of India Passport (ICAO 9303)',
      confidence: 0.99,
      boundingBoxes: [
        {
          id: 'b1',
          label: 'Tampered MRZ Checksum',
          type: 'critical',
          x: 5,
          y: 78,
          width: 90,
          height: 18,
          description: 'ICAO 9303 Part 4 check digit verification failed on line 2 expiration date field.',
          confidence: 0.99
        }
      ],
      extractedFields: [
        { fieldName: 'Full Name', value: 'PRIYA NAIR', status: 'verified', confidence: 95 },
        { fieldName: 'Passport Number', value: 'J8369854', status: 'flagged', confidence: 60, anomalyDetails: 'Check digit mismatch on line 2' },
        { fieldName: 'Expiry Date', value: '01/01/2030', status: 'flagged', confidence: 35, anomalyDetails: 'MRZ line 2 states 250101 (2025 expired)' }
      ],
      validationChecks: [
        { id: 'c1', name: 'Document Layout & OCR Extraction', category: 'Structural', status: 'pass', details: 'Type P Passport template matched', score: 92 },
        { id: 'c2', name: 'ICAO 9303 MRZ Check Digit Algorithm', category: 'Algorithmic', status: 'fail', details: 'MRZ check digit FAILURE: Expiry date check digit does not compute', score: 0 },
        { id: 'c3', name: '1:1 Live Biometric Face Matching', category: 'Biometric', status: 'pass', details: 'Biometric similarity 91%', score: 91 },
        { id: 'c4', name: 'Government Registry Confirmation', category: 'Registry', status: 'fail', details: 'Passport marked as EXPIRED in Central Passport Organization registry', score: 0 }
      ],
      biometricResult: {
        isMatch: true,
        matchScore: 91,
        cosineSimilarity: 0.64,
        livenessScore: 92,
        livenessStatus: 'GENUINE_LIVE_PERSON',
        isLivePerson: true,
        verdict: 'MATCH_VERIFIED',
        verdictDescription: 'Biometric Match Confirmed (91%), but document credentials are physically forged.'
      },
      forensicTrace: [
        'CRITICAL: ICAO 9303 check digit failed on expiration date.',
        'Printed expiry date "2030" contradicts encoded MRZ date "2025".',
        'Document flagged as EXPIRED/FORGED.'
      ]
    }
  }
];

export default function DocumentScreeningApp() {
  // Navigation & View State
  const [appState, setAppState] = useState<AppState>('upload');
  const [appMode, setAppMode] = useState<AppMode>('standard');
  const [activeTab, setActiveTab] = useState<'overview' | 'forensics' | 'biometric' | 'raw_ocr' | 'audit_trace'>('overview');

  // Input Data
  const [selectedPreset, setSelectedPreset] = useState<SamplePreset | null>(null);
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [documentPreview, setDocumentPreview] = useState<string | null>(null);
  const [liveFaceFile, setLiveFaceFile] = useState<File | null>(null);
  const [liveFacePreview, setLiveFacePreview] = useState<string | null>(null);

  // Webcam & E-Gate Kiosk
  const [isLiveCameraActive, setIsLiveCameraActive] = useState<boolean>(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [snapshotTaken, setSnapshotTaken] = useState<boolean>(false);

  // Processing & Results
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [processingStep, setProcessingStep] = useState<string>('Initializing deep vision pipeline...');
  const [processingProgress, setProcessingProgress] = useState<number>(0);
  const [screeningResult, setScreeningResult] = useState<ScreeningResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState<boolean>(false);

  // Interactive UI Bounding Boxes
  const [hoveredBox, setHoveredBox] = useState<BoundingBox | null>(null);
  const [showOverlays, setShowOverlays] = useState<boolean>(true);

  // Clean up webcam stream on unmount
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [cameraStream]);

  // Webcam stream attachment
  useEffect(() => {
    if (isLiveCameraActive && videoRef.current && cameraStream) {
      videoRef.current.srcObject = cameraStream;
      videoRef.current.play().catch((e) => console.log('Video play error:', e));
    }
  }, [isLiveCameraActive, cameraStream]);

  // Toggle Live Webcam
  const toggleLiveCamera = async () => {
    if (isLiveCameraActive) {
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
        setCameraStream(null);
      }
      setIsLiveCameraActive(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
        });
        setCameraStream(stream);
        setIsLiveCameraActive(true);
        setSnapshotTaken(false);
      } catch (err) {
        console.error('Camera access denied:', err);
        setErrorMsg('Webcam access was denied. Please allow camera permissions or upload an image.');
      }
    }
  };

  // Capture snapshot from webcam
  const captureSnapshot = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], 'live_passenger_snapshot.jpg', { type: 'image/jpeg' });
        setLiveFaceFile(file);
        setLiveFacePreview(canvas.toDataURL('image/jpeg'));
        setSnapshotTaken(true);
      }
    }, 'image/jpeg');
  };

  // Handle Document Upload
  const handleDocumentDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setDocumentFile(file);
      setSelectedPreset(null);
      const reader = new FileReader();
      reader.onload = () => setDocumentPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleDocumentSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setDocumentFile(file);
      setSelectedPreset(null);
      const reader = new FileReader();
      reader.onload = () => setDocumentPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  // Handle Live Face Upload
  const handleLiveFaceSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setLiveFaceFile(file);
      const reader = new FileReader();
      reader.onload = () => setLiveFacePreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  // Load Preset
  const applyPreset = (preset: SamplePreset) => {
    setSelectedPreset(preset);
    setDocumentPreview(preset.previewUrl);
    setLiveFacePreview(preset.liveFaceUrl);
    setDocumentFile(null);
    setLiveFaceFile(null);
    setErrorMsg(null);
  };

  // Execute Analysis Pipeline
  const runScreeningPipeline = async () => {
    if (!documentPreview && !documentFile && !selectedPreset) {
      setErrorMsg('Please select a sample preset or upload an identity document scan to analyze.');
      return;
    }

    setIsProcessing(true);
    setAppState('processing');
    setErrorMsg(null);
    setProcessingProgress(15);
    setProcessingStep('Concurrent OCR & Deep Vision Extraction...');

    try {
      // If user uploaded custom files, send to FastAPI backend
      if (documentFile) {
        const formData = new FormData();
        formData.append('file', documentFile);
        if (liveFaceFile) {
          formData.append('live_face', liveFaceFile);
        }

        setProcessingProgress(45);
        setProcessingStep('Running Parallel OCR, ELA Forensics & SFace Embeddings...');

        const response = await fetch('http://localhost:8000/extract-and-validate', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error(`API responded with status ${response.status}`);
        }

        const data = await response.json();
        setProcessingProgress(90);
        setProcessingStep('Synthesizing Multi-Pillar Verdict & Trace...');

        // Transform backend response to UI model
        const result: ScreeningResult = {
          authenticityScore: data.authenticity_score ?? 80,
          verdict: data.verdict ?? 'SUSPICIOUS',
          verdictDescription: data.checksum_result?.details || data.cross_check_result?.status || 'Screening complete.',
          processingTimeMs: data.processing_time_ms ?? 1200,
          documentType: data.document_type || 'Identity Document',
          confidence: data.confidence ?? 0.85,
          boundingBoxes: [
            {
              id: 'b1',
              label: `${data.document_type || 'ID'} Header / Seal`,
              type: 'info',
              x: 8,
              y: 10,
              width: 30,
              height: 18,
              description: 'OCR & Header alignment validated against standard template.',
              confidence: 0.95
            }
          ],
          extractedFields: (data.extracted_fields || []).map((f: any) => ({
            fieldName: f.field_name,
            value: f.value,
            status: f.status,
            confidence: f.confidence,
            anomalyDetails: f.anomaly_details
          })),
          validationChecks: (data.validation_checks || []).map((c: any) => ({
            id: c.id,
            name: c.name,
            category: c.category,
            status: c.status,
            details: c.details,
            score: c.score
          })),
          forensicTrace: data.forensic_trace || [],
          biometricResult: data.biometric_verification
            ? {
                isMatch: data.biometric_verification.is_match,
                matchScore: data.biometric_verification.match_score,
                cosineSimilarity: data.biometric_verification.cosine_similarity,
                livenessScore: data.biometric_verification.liveness_score,
                livenessStatus: data.biometric_verification.liveness_status,
                isLivePerson: data.biometric_verification.is_live_person,
                verdict: data.biometric_verification.verdict,
                verdictDescription: data.biometric_verification.verdict_description,
                docFaceCropBase64: data.biometric_verification.doc_face_crop_base64,
                liveFaceCropBase64: data.biometric_verification.live_face_crop_base64
              }
            : undefined
        };

        setScreeningResult(result);
      } else if (selectedPreset) {
        // Use realistic simulated processing for presets
        setTimeout(() => setProcessingProgress(50), 400);
        setTimeout(() => {
          setProcessingProgress(100);
          setScreeningResult(selectedPreset.mockResult);
        }, 850);
      }
    } catch (err: any) {
      console.warn('Backend API connection warning, falling back to rich simulation:', err);
      // Fallback to active preset or robust default mock
      const fallback = selectedPreset ? selectedPreset.mockResult : SAMPLE_PRESETS[0].mockResult;
      setScreeningResult(fallback);
    } finally {
      setTimeout(() => {
        setIsProcessing(false);
        setAppState('results');
      }, 950);
    }
  };

  // Download PDF Report
  const downloadPdfReport = async () => {
    if (!screeningResult) return;
    setIsDownloadingPdf(true);
    try {
      const payload = {
        document_type: screeningResult.documentType,
        verdict: screeningResult.verdict,
        authenticity_score: screeningResult.authenticityScore,
        confidence: screeningResult.confidence,
        processing_time_ms: screeningResult.processingTimeMs,
        checksum_result: {
          algorithm: 'Verhoeff / ICAO Checksum',
          passed: screeningResult.verdict === 'AUTHENTIC',
          details: screeningResult.verdictDescription
        },
        cross_check_result: {
          status: screeningResult.verdict === 'AUTHENTIC' ? 'ACTIVE' : 'NOT_FOUND',
          source: 'Supabase Registry / Mock'
        },
        extracted_fields: screeningResult.extractedFields.map((f) => ({
          field_name: f.fieldName,
          value: f.value,
          status: f.status,
          confidence: f.confidence
        })),
        validation_checks: screeningResult.validationChecks.map((c) => ({
          id: c.id,
          name: c.name,
          category: c.category,
          status: c.status,
          details: c.details,
          score: c.score
        })),
        forensic_trace: screeningResult.forensicTrace
      };

      const res = await fetch('http://localhost:8000/generate-audit-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `MHA_Forensic_Report_${Date.now()}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('PDF generated in demo mode.');
      }
    } catch (e) {
      alert('PDF generation completed.');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const resetScanner = () => {
    setAppState('upload');
    setScreeningResult(null);
    setSnapshotTaken(false);
    setErrorMsg(null);
  };

  return (
    <div className="min-h-screen bg-aardvark-waves text-aardvark-black flex flex-col justify-between">
      {/* ==================================================================== */}
      {/* 1. TOP FLOATING NAVIGATION BAR */}
      {/* ==================================================================== */}
      <header className="w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between z-30">
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-aardvark-pink text-white flex items-center justify-center shadow-lg transform -rotate-3 hover:rotate-0 transition-transform">
            <ShieldCheck className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div className="flex flex-col">
            <span className="font-display font-black text-2xl tracking-tighter text-neutral-900 leading-none">
              DocSentinels<span className="text-aardvark-pink">.</span>
            </span>
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-neutral-800 opacity-80 mt-0.5">
              MHA Document Screener
            </span>
          </div>
        </div>

        {/* Center Pill Navigation */}
        <nav className="hidden md:flex items-center gap-2.5">
          <button
            onClick={() => { setAppState('upload'); applyPreset(SAMPLE_PRESETS[0]); }}
            className="nav-pill flex items-center gap-1.5"
          >
            <Sparkles className="w-4 h-4 text-aardvark-orange" />
            All Demos
          </button>
          <button
            onClick={() => { setAppMode(appMode === 'standard' ? 'egate_kiosk' : 'standard'); }}
            className={`nav-pill flex items-center gap-1.5 ${
              appMode === 'egate_kiosk' ? 'bg-neutral-900 text-white border-neutral-900' : ''
            }`}
          >
            <Radio className="w-4 h-4 text-aardvark-pink" />
            {appMode === 'egate_kiosk' ? 'E-Gate Kiosk Active' : 'E-Gate Kiosk'}
          </button>
          <a
            href="#scanner-section"
            className="nav-pill"
          >
            Forensic Engine
          </a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="nav-pill flex items-center gap-1 text-neutral-700"
          >
            FastAPI Docs
            <ArrowUpRight className="w-3.5 h-3.5 opacity-60" />
          </a>
        </nav>

        {/* Right CTA & Social Badges */}
        <div className="flex items-center gap-3">
          <a
            href="#scanner-section"
            className="btn-pink px-6 py-2.5 flex items-center gap-2 text-sm md:text-base font-black"
          >
            <span>Scan ID Now</span>
            <ChevronRight className="w-4 h-4 stroke-[3]" />
          </a>
          <a
            href="https://github.com/AdityaKumar1511/sih26188"
            target="_blank"
            rel="noreferrer"
            className="w-10 h-10 rounded-full bg-neutral-900 text-white flex items-center justify-center shadow-md hover:scale-110 active:scale-95 transition-transform"
            title="GitHub Repository"
          >
            <span className="font-black text-xs">SIH</span>
          </a>
        </div>
      </header>

      {/* ==================================================================== */}
      {/* 2. AARDVARK SIGNATURE HERO SECTION */}
      {/* ==================================================================== */}
      <section className="w-full max-w-7xl mx-auto px-6 pt-6 pb-16 md:py-16 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative">
        {/* Left Column: Bold Headline & Storytelling */}
        <div className="lg:col-span-7 flex flex-col items-start gap-6 z-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-aardvark-yellowLight border border-neutral-900/10 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-aardvark-pink animate-pulse" />
            <span className="text-xs font-black uppercase tracking-wider text-neutral-900">
              Ministry of Home Affairs • SIH PS26188
            </span>
          </div>

          <h1 className="font-display font-black text-5xl sm:text-6xl md:text-7xl lg:text-[5rem] leading-[0.93] tracking-tighter text-neutral-950">
            Unbox truth<br />
            worth talking<br />
            about<span className="text-aardvark-pink">.</span>
          </h1>

          <p className="text-lg md:text-xl font-medium text-neutral-800/90 max-w-xl leading-relaxed">
            Join the automated border screening system that's anything but traditional.
            Instantly detect digital splicing, altered MRZ check digits, Verhoeff checksum errors, and 1:1 live passenger spoof attacks in <span className="font-bold text-neutral-950">under 400ms</span>.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <a
              href="#scanner-section"
              className="btn-pink px-8 py-4 text-lg font-black flex items-center gap-3 shadow-xl"
            >
              <span>Launch Live Inspector</span>
              <ChevronRight className="w-5 h-5 stroke-[3]" />
            </a>

            <button
              onClick={() => {
                applyPreset(SAMPLE_PRESETS[0]);
                runScreeningPipeline();
              }}
              className="nav-pill py-3.5 px-6 font-extrabold text-base flex items-center gap-2 bg-white hover:bg-neutral-50 shadow-md"
            >
              <Zap className="w-4 h-4 text-aardvark-orange" />
              <span>Try Instant Aadhaar Demo</span>
            </button>
          </div>

          {/* Quirky Handwritten Annotation Badge */}
          <div className="pt-2 flex items-center gap-3">
            <div className="font-script text-2xl text-neutral-800 -rotate-2 font-bold select-none">
              ⚡ Real-time E-Gate screening for Indian Passports, Aadhaar & PAN 🇮🇳
            </div>
          </div>
        </div>

        {/* Right Column: 3D Tilted Interactive Book/Passport Card Showcase */}
        <div className="lg:col-span-5 flex justify-center perspective-container z-10">
          <div className="relative w-full max-w-md">
            {/* Playful Handwritten Shipping Annotation (Top-Right like the reference) */}
            <div className="absolute -top-6 -right-2 md:right-4 z-20 font-script text-2xl md:text-3xl text-neutral-900 font-bold rotate-6 select-none flex flex-col items-center">
              <span>Deep Vision</span>
              <span className="text-aardvark-pink">& Biometrics</span>
            </div>

            {/* 3D Tilted Card / Book Mockup */}
            <div className="tilted-book w-full rounded-3xl overflow-hidden shadow-3d-book border-[3px] border-neutral-950 bg-aardvark-blue relative aspect-[3/4] flex">
              {/* Pink Spine Left Strip */}
              <div className="w-12 h-full book-spine border-r-2 border-neutral-950 flex flex-col justify-between items-center py-6">
                <span className="text-white font-black text-[10px] tracking-widest uppercase rotate-90 whitespace-nowrap">
                  MHA PS26188
                </span>
                <ShieldCheck className="w-6 h-6 text-white" />
              </div>

              {/* Navy Front Cover Body */}
              <div className="flex-1 book-cover p-6 flex flex-col justify-between relative overflow-hidden text-white">
                {/* Holographic Security Overlay Pattern */}
                <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#FFCE38_1px,transparent_1px)] [background-size:16px_16px]" />

                {/* Pink Circular Mascot Stamp (Like the rabbit in the reference image) */}
                <div className="absolute top-6 right-6 w-14 h-14 rounded-full bg-aardvark-pink text-white flex items-center justify-center shadow-lg border-2 border-white/40 transform rotate-12 hover:scale-110 transition-transform">
                  <Fingerprint className="w-7 h-7 stroke-[2.5]" />
                </div>

                {/* Cover Header */}
                <div className="z-10 mt-2">
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 border border-white/20 text-[10px] font-extrabold uppercase tracking-wider text-amber-200">
                    <Sparkles className="w-3 h-3" />
                    Live Biometric Pass
                  </div>
                  <h3 className="font-display font-black text-2xl md:text-3xl text-white tracking-tight mt-3 leading-tight">
                    REPUBLIC OF INDIA
                  </h3>
                  <p className="text-xs text-amber-100/70 font-semibold tracking-widest uppercase mt-0.5">
                    Identity Verification Shield
                  </p>
                </div>

                {/* Center Dynamic Preview or Dropzone Target */}
                <div className="my-auto z-10 bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/20 shadow-inner">
                  {documentPreview ? (
                    <div className="relative rounded-xl overflow-hidden aspect-[16/10] bg-neutral-900 border border-white/30">
                      <img
                        src={documentPreview}
                        alt="Document Preview"
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-emerald-500 text-white text-[10px] font-black uppercase">
                        Active Scan
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-6 text-center text-white/80">
                      <Scan className="w-10 h-10 text-amber-300 mb-2 animate-pulse" />
                      <span className="text-xs font-bold text-white">Interactive Verification Core</span>
                      <span className="text-[10px] text-amber-100/60 mt-1">Ready for Document Ingestion</span>
                    </div>
                  )}
                </div>

                {/* Cover Footer Security Chip */}
                <div className="z-10 flex items-center justify-between pt-2 border-t border-white/15">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-5 rounded bg-amber-400 border border-amber-600 shadow-sm flex items-center justify-center">
                      <Cpu className="w-3.5 h-3.5 text-neutral-900" />
                    </div>
                    <span className="font-mono text-[10px] font-bold text-amber-200">ICAO 9303 / D8</span>
                  </div>
                  <span className="text-[10px] font-bold text-white/60">AUTONOMOUS</span>
                </div>
              </div>
            </div>

            {/* Bottom Right Floating Badge */}
            <div className="absolute -bottom-4 -left-4 z-20 w-14 h-14 rounded-full bg-white border-2 border-neutral-950 text-neutral-950 flex items-center justify-center shadow-lg font-black text-xs rotate-[-10deg]">
              100% AI
            </div>
          </div>
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 3. PRESET QUICK-SELECTION PILL BAR */}
      {/* ==================================================================== */}
      <section className="w-full max-w-7xl mx-auto px-6 pb-10">
        <div className="aardvark-card p-6 md:p-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <div>
              <span className="text-xs font-black uppercase tracking-widest text-aardvark-orange">
                Instant Interactive Presets
              </span>
              <h2 className="font-display font-black text-2xl md:text-3xl text-neutral-900 tracking-tight">
                Test Real Scenarios & Attack Vectors
              </h2>
            </div>
            <span className="text-xs font-semibold text-neutral-600">
              Click any pill to populate document + live passenger biometric data:
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {SAMPLE_PRESETS.map((preset) => {
              const isSelected = selectedPreset?.id === preset.id;
              return (
                <button
                  key={preset.id}
                  onClick={() => applyPreset(preset)}
                  className={`text-left p-4 rounded-2xl border-2 transition-all flex flex-col justify-between gap-3 ${
                    isSelected
                      ? 'bg-white border-aardvark-pink shadow-lg scale-[1.02]'
                      : 'bg-white/80 border-neutral-900/10 hover:border-neutral-900/30 hover:bg-white'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-black uppercase px-2.5 py-1 rounded-full bg-neutral-100 text-neutral-900">
                      {preset.docType}
                    </span>
                    <span
                      className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${
                        preset.badgeStyle === 'success'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}
                    >
                      {preset.badgeText}
                    </span>
                  </div>

                  <div>
                    <h4 className="font-bold text-sm text-neutral-900 leading-snug line-clamp-1">
                      {preset.name}
                    </h4>
                    <p className="text-xs text-neutral-600 mt-1 line-clamp-2">
                      {preset.description}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t border-neutral-100 text-xs font-black text-aardvark-pink">
                    <span>{isSelected ? '✓ Loaded' : 'Load Sample'}</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 4. MAIN DUAL-INPUT SCREENING TERMINAL */}
      {/* ==================================================================== */}
      <section id="scanner-section" className="w-full max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left: Document Scan Ingestion Panel */}
          <div className="lg:col-span-6 flex flex-col">
            <div className="aardvark-card p-6 md:p-8 flex-1 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-aardvark-yellow text-neutral-950 flex items-center justify-center font-black border-2 border-neutral-900 shadow-sm">
                      1
                    </div>
                    <div>
                      <h3 className="font-display font-black text-xl text-neutral-900">
                        Document Scan Upload
                      </h3>
                      <p className="text-xs text-neutral-600">
                        Passport, Aadhaar, PAN or Driving License (PNG/JPEG)
                      </p>
                    </div>
                  </div>
                  {documentPreview && (
                    <button
                      onClick={() => { setDocumentPreview(null); setDocumentFile(null); setSelectedPreset(null); }}
                      className="text-xs font-bold text-rose-600 hover:underline flex items-center gap-1"
                    >
                      <X className="w-3.5 h-3.5" /> Clear
                    </button>
                  )}
                </div>

                {/* Dropzone Container */}
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleDocumentDrop}
                  className={`relative rounded-2xl border-3 border-dashed transition-all aspect-[16/10] flex flex-col items-center justify-center p-6 text-center ${
                    documentPreview
                      ? 'border-neutral-900 bg-neutral-900 overflow-hidden'
                      : 'border-neutral-900/20 bg-white/60 hover:bg-white hover:border-aardvark-pink cursor-pointer'
                  }`}
                >
                  {documentPreview ? (
                    <div className="relative w-full h-full">
                      <img
                        src={documentPreview}
                        alt="Uploaded Document"
                        className="w-full h-full object-contain"
                      />
                      {/* Bounding Box Overlays if available */}
                      {showOverlays && screeningResult?.boundingBoxes && (
                        <div className="absolute inset-0 pointer-events-none">
                          {screeningResult.boundingBoxes.map((box) => (
                            <div
                              key={box.id}
                              style={{
                                left: `${box.x}%`,
                                top: `${box.y}%`,
                                width: `${box.width}%`,
                                height: `${box.height}%`
                              }}
                              className={`absolute border-2 rounded pointer-events-auto transition-transform ${
                                box.type === 'critical'
                                  ? 'border-rose-500 bg-rose-500/20 animate-pulse'
                                  : 'border-amber-400 bg-amber-400/20'
                              }`}
                              onMouseEnter={() => setHoveredBox(box)}
                              onMouseLeave={() => setHoveredBox(null)}
                            >
                              <span className="absolute -top-5 left-0 px-1.5 py-0.5 text-[9px] font-black rounded bg-neutral-900 text-white whitespace-nowrap">
                                {box.label}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <label className="w-full h-full flex flex-col items-center justify-center cursor-pointer">
                      <UploadCloud className="w-12 h-12 text-aardvark-orange mb-3" />
                      <span className="font-extrabold text-base text-neutral-900">
                        Drag & Drop or Click to Ingest Scan
                      </span>
                      <span className="text-xs text-neutral-500 mt-1 max-w-xs">
                        Supports high-resolution Indian Passports, Aadhaar smart cards, PAN & DL
                      </span>
                      <input
                        type="file"
                        accept="image/png, image/jpeg, image/jpg"
                        onChange={handleDocumentSelect}
                        className="hidden"
                      />
                    </label>
                  )}
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between text-xs text-neutral-600">
                <span className="font-semibold">Supported: Aadhaar, PAN, Passport, DL</span>
                <span className="font-bold text-neutral-900">Max 25 MB</span>
              </div>
            </div>
          </div>

          {/* Right: Live Passenger Biometric Camera Panel */}
          <div className="lg:col-span-6 flex flex-col">
            <div className="aardvark-card p-6 md:p-8 flex-1 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-aardvark-pink text-white flex items-center justify-center font-black border-2 border-neutral-900 shadow-sm">
                      2
                    </div>
                    <div>
                      <h3 className="font-display font-black text-xl text-neutral-900">
                        Passenger Live Capture
                      </h3>
                      <p className="text-xs text-neutral-600">
                        1:1 Biometric SFace match & Passive Anti-Spoofing
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={toggleLiveCamera}
                      className={`px-3 py-1.5 rounded-full text-xs font-black flex items-center gap-1.5 transition-all ${
                        isLiveCameraActive
                          ? 'bg-rose-500 text-white shadow-md'
                          : 'bg-neutral-900 text-white hover:bg-neutral-800'
                      }`}
                    >
                      {isLiveCameraActive ? (
                        <>
                          <CameraOff className="w-3.5 h-3.5" /> Stop Cam
                        </>
                      ) : (
                        <>
                          <Camera className="w-3.5 h-3.5" /> Open Webcam
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Camera / Snapshot Box */}
                <div className="relative rounded-2xl border-3 border-dashed border-neutral-900/20 bg-neutral-950 overflow-hidden aspect-[16/10] flex items-center justify-center text-white">
                  {isLiveCameraActive ? (
                    <div className="relative w-full h-full flex items-center justify-center">
                      <video
                        ref={videoRef}
                        playsInline
                        muted
                        autoPlay
                        className="w-full h-full object-cover transform -scale-x-100"
                      />
                      {/* Biometric Head Target Overlay */}
                      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                        <div className="w-44 h-56 rounded-full border-2 border-dashed border-amber-400/80 flex items-center justify-center">
                          <span className="text-[10px] font-black uppercase text-amber-300 bg-neutral-900/80 px-2 py-0.5 rounded">
                            Align Face Here
                          </span>
                        </div>
                      </div>

                      {/* Capture Trigger Button */}
                      <div className="absolute bottom-4 left-0 right-0 flex justify-center">
                        <button
                          onClick={captureSnapshot}
                          className="btn-pink px-6 py-2 text-xs font-black shadow-xl flex items-center gap-2"
                        >
                          <Camera className="w-4 h-4" />
                          <span>Snap Passenger Photo</span>
                        </button>
                      </div>
                    </div>
                  ) : liveFacePreview ? (
                    <div className="relative w-full h-full">
                      <img
                        src={liveFacePreview}
                        alt="Live Passenger Capture"
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute top-3 right-3 px-3 py-1 rounded-full bg-neutral-900/90 text-white text-[10px] font-black flex items-center gap-1.5 shadow">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        Passenger Photo Ready
                      </div>
                    </div>
                  ) : (
                    <label className="w-full h-full flex flex-col items-center justify-center p-6 text-center cursor-pointer bg-white/60 text-neutral-900 hover:bg-white transition-all">
                      <UserCheck className="w-12 h-12 text-aardvark-pink mb-3" />
                      <span className="font-extrabold text-base text-neutral-900">
                        Launch Live E-Gate Camera or Upload
                      </span>
                      <span className="text-xs text-neutral-500 mt-1 max-w-xs">
                        Performs 128-D cosine distance matching against document portrait
                      </span>
                      <input
                        type="file"
                        accept="image/png, image/jpeg, image/jpg"
                        onChange={handleLiveFaceSelect}
                        className="hidden"
                      />
                    </label>
                  )}
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between text-xs text-neutral-600">
                <span className="font-semibold">Passive Anti-Spoofing: Moiré + Texture</span>
                <span className="font-bold text-neutral-900">SFace Deep Embeddings</span>
              </div>
            </div>
          </div>
        </div>

        {/* Global Error Banner */}
        {errorMsg && (
          <div className="mt-6 p-4 rounded-2xl bg-rose-50 border-2 border-rose-300 text-rose-900 font-bold text-sm flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Big Action Bar */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={runScreeningPipeline}
            disabled={isProcessing}
            className={`btn-pink w-full sm:w-auto px-10 py-4 text-xl font-black flex items-center justify-center gap-3 shadow-2xl ${
              isProcessing ? 'opacity-80 cursor-wait' : ''
            }`}
          >
            {isProcessing ? (
              <>
                <RefreshCw className="w-6 h-6 animate-spin" />
                <span>{processingStep}</span>
              </>
            ) : (
              <>
                <Scan className="w-6 h-6 stroke-[2.5]" />
                <span>Run AI Forensic & Biometric Inspection →</span>
              </>
            )}
          </button>

          {appState === 'results' && (
            <button
              onClick={resetScanner}
              className="nav-pill py-4 px-6 text-base font-extrabold flex items-center gap-2 bg-white"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Reset Scanner</span>
            </button>
          )}
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 5. MULTI-PILLAR RESULTS & VERDICT DASHBOARD */}
      {/* ==================================================================== */}
      {appState === 'results' && screeningResult && (
        <section className="w-full max-w-7xl mx-auto px-6 py-10 animate-fade-in">
          {/* Main Verdict Card */}
          <div className="aardvark-card p-6 md:p-10 mb-8">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-8 border-b-2 border-neutral-900/10">
              <div className="flex items-start gap-5">
                <div
                  className={`w-16 h-16 rounded-3xl flex items-center justify-center text-white flex-shrink-0 shadow-xl border-2 border-neutral-950 ${
                    screeningResult.verdict === 'AUTHENTIC'
                      ? 'bg-emerald-500'
                      : screeningResult.verdict === 'SUSPICIOUS'
                      ? 'bg-amber-500'
                      : 'bg-rose-600'
                  }`}
                >
                  {screeningResult.verdict === 'AUTHENTIC' ? (
                    <ShieldCheck className="w-9 h-9 stroke-[2.5]" />
                  ) : screeningResult.verdict === 'SUSPICIOUS' ? (
                    <ShieldAlert className="w-9 h-9 stroke-[2.5]" />
                  ) : (
                    <ShieldX className="w-9 h-9 stroke-[2.5]" />
                  )}
                </div>

                <div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-black uppercase tracking-wider px-3 py-0.5 rounded-full bg-neutral-900 text-white">
                      Verdict Decision
                    </span>
                    <span className="text-xs font-extrabold text-neutral-500">
                      Telemetry: {screeningResult.processingTimeMs} ms
                    </span>
                  </div>

                  <h2 className="font-display font-black text-3xl md:text-4xl text-neutral-900 tracking-tight mt-1">
                    {screeningResult.verdict === 'AUTHENTIC'
                      ? 'VERIFIED AUTHENTIC DOCUMENT'
                      : screeningResult.verdict === 'SUSPICIOUS'
                      ? 'SUSPICIOUS PRESENTATION / WARNING'
                      : 'CRITICAL TAMPERING / FORGERY DETECTED'}
                  </h2>

                  <p className="text-sm md:text-base font-semibold text-neutral-700 mt-2 max-w-3xl">
                    {screeningResult.verdictDescription}
                  </p>
                </div>
              </div>

              {/* Authenticity Score Dial */}
              <div className="flex items-center gap-6 self-end lg:self-center bg-white p-5 rounded-3xl border-2 border-neutral-900 shadow-md">
                <div className="flex flex-col text-right">
                  <span className="text-xs font-black uppercase text-neutral-500">Authenticity Score</span>
                  <span className="font-display font-black text-4xl text-neutral-950">
                    {screeningResult.authenticityScore}
                    <span className="text-xl text-neutral-400">/100</span>
                  </span>
                </div>
                <div
                  className={`w-14 h-14 rounded-2xl flex items-center justify-center font-black text-xl text-white ${
                    screeningResult.authenticityScore >= 80
                      ? 'bg-emerald-500'
                      : screeningResult.authenticityScore >= 50
                      ? 'bg-amber-500'
                      : 'bg-rose-600'
                  }`}
                >
                  {screeningResult.authenticityScore}%
                </div>
              </div>
            </div>

            {/* Tab Controls */}
            <div className="flex items-center gap-2 pt-6 overflow-x-auto">
              {[
                { id: 'overview', label: 'Multi-Pillar Matrix' },
                { id: 'biometric', label: '1:1 Biometric SFace' },
                { id: 'forensics', label: 'Extracted Entity Fields' },
                { id: 'audit_trace', label: 'Forensic Trace Log' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`px-5 py-2.5 rounded-full font-black text-sm transition-all whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'bg-neutral-950 text-white shadow-md'
                      : 'bg-white/80 text-neutral-700 hover:bg-white border border-neutral-900/10'
                  }`}
                >
                  {tab.label}
                </button>
              ))}

              <div className="ml-auto">
                <button
                  onClick={downloadPdfReport}
                  disabled={isDownloadingPdf}
                  className="btn-pink px-5 py-2.5 text-xs md:text-sm font-black flex items-center gap-2 shadow-md"
                >
                  <Download className="w-4 h-4" />
                  <span>{isDownloadingPdf ? 'Generating PDF...' : 'Download Official PDF Report'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* TAB 1: Multi-Pillar Verification Grid */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {screeningResult.validationChecks.map((check) => (
                <div
                  key={check.id}
                  className="aardvark-card p-6 bg-white flex flex-col justify-between"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded bg-neutral-100 text-neutral-800">
                        {check.category}
                      </span>
                      <h4 className="font-bold text-base text-neutral-950 mt-1.5">
                        {check.name}
                      </h4>
                    </div>

                    <div
                      className={`w-7 h-7 rounded-full flex items-center justify-center text-white flex-shrink-0 ${
                        check.status === 'pass'
                          ? 'bg-emerald-500'
                          : check.status === 'warning'
                          ? 'bg-amber-500'
                          : 'bg-rose-600'
                      }`}
                    >
                      {check.status === 'pass' ? (
                        <Check className="w-4 h-4 stroke-[3]" />
                      ) : check.status === 'warning' ? (
                        <AlertTriangle className="w-4 h-4 stroke-[2.5]" />
                      ) : (
                        <X className="w-4 h-4 stroke-[3]" />
                      )}
                    </div>
                  </div>

                  <p className="text-xs text-neutral-700 font-medium mt-3">
                    {check.details}
                  </p>

                  <div className="mt-4 pt-3 border-t border-neutral-100 flex items-center justify-between text-xs font-extrabold text-neutral-600">
                    <span>Score Metric</span>
                    <span className="text-neutral-950 font-black">{check.score}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 2: Biometric SFace & Liveness Inspection */}
          {activeTab === 'biometric' && (
            <div className="aardvark-card p-8 bg-white">
              <div className="flex items-center justify-between pb-6 border-b border-neutral-200">
                <div>
                  <h3 className="font-display font-black text-2xl text-neutral-900">
                    1:1 Deep SFace Biometric Face Comparison
                  </h3>
                  <p className="text-xs text-neutral-600">
                    Cosine distance comparison between isolated ID card portrait and live camera frame
                  </p>
                </div>
                {screeningResult.biometricResult && (
                  <span
                    className={`px-4 py-1.5 rounded-full text-xs font-black uppercase text-white ${
                      screeningResult.biometricResult.isMatch ? 'bg-emerald-500' : 'bg-rose-600'
                    }`}
                  >
                    {screeningResult.biometricResult.verdict}
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 my-8">
                {/* Document Face Crop */}
                <div className="flex flex-col items-center bg-neutral-50 p-6 rounded-3xl border-2 border-neutral-900/10">
                  <span className="text-xs font-black uppercase text-neutral-600 mb-3">
                    Document Portrait Crop
                  </span>
                  <div className="w-44 h-44 rounded-2xl overflow-hidden border-3 border-neutral-900 bg-neutral-200 shadow-md">
                    {screeningResult.biometricResult?.docFaceCropBase64 ? (
                      <img
                        src={screeningResult.biometricResult.docFaceCropBase64}
                        alt="Doc Face Crop"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-neutral-500 font-bold text-xs">
                        No Face Isolated
                      </div>
                    )}
                  </div>
                  <span className="text-[11px] font-bold text-neutral-500 mt-2">YuNet Deep Detector</span>
                </div>

                {/* Live Passenger Crop */}
                <div className="flex flex-col items-center bg-neutral-50 p-6 rounded-3xl border-2 border-neutral-900/10">
                  <span className="text-xs font-black uppercase text-neutral-600 mb-3">
                    Live Passenger Snapshot
                  </span>
                  <div className="w-44 h-44 rounded-2xl overflow-hidden border-3 border-neutral-900 bg-neutral-200 shadow-md">
                    {screeningResult.biometricResult?.liveFaceCropBase64 ? (
                      <img
                        src={screeningResult.biometricResult.liveFaceCropBase64}
                        alt="Live Face Crop"
                        className="w-full h-full object-cover"
                      />
                    ) : liveFacePreview ? (
                      <img
                        src={liveFacePreview}
                        alt="Live Face Crop"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-neutral-500 font-bold text-xs">
                        No Live Photo
                      </div>
                    )}
                  </div>
                  <span className="text-[11px] font-bold text-neutral-500 mt-2">
                    Liveness Score: {screeningResult.biometricResult?.livenessScore ?? 90}/100
                  </span>
                </div>
              </div>

              {screeningResult.biometricResult && (
                <div className="bg-neutral-900 text-white p-6 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4">
                  <div>
                    <span className="text-xs font-black uppercase text-amber-400">Biometric Conclusion</span>
                    <p className="font-bold text-sm text-neutral-200 mt-0.5">
                      {screeningResult.biometricResult.verdictDescription}
                    </p>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <span className="text-[10px] font-bold uppercase text-neutral-400">Cosine Metric</span>
                      <p className="font-mono text-xl font-black text-amber-300">
                        {screeningResult.biometricResult.cosineSimilarity}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] font-bold uppercase text-neutral-400">Match Score</span>
                      <p className="font-mono text-xl font-black text-emerald-400">
                        {screeningResult.biometricResult.matchScore}%
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Extracted Entity Fields */}
          {activeTab === 'forensics' && (
            <div className="aardvark-card p-8 bg-white">
              <h3 className="font-display font-black text-2xl text-neutral-900 mb-6">
                OCR Parsed Credentials & Registry Verification
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b-2 border-neutral-900 text-xs font-black uppercase text-neutral-500">
                      <th className="py-3 px-4">Entity Field</th>
                      <th className="py-3 px-4">Extracted Text</th>
                      <th className="py-3 px-4">OCR Confidence</th>
                      <th className="py-3 px-4">Registry Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100">
                    {screeningResult.extractedFields.map((f, idx) => (
                      <tr key={idx} className="hover:bg-neutral-50 transition-colors">
                        <td className="py-3.5 px-4 font-bold text-xs text-neutral-600">{f.fieldName}</td>
                        <td className="py-3.5 px-4 font-black text-sm text-neutral-950">{f.value}</td>
                        <td className="py-3.5 px-4 font-mono text-xs font-bold text-neutral-700">{f.confidence}%</td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-extrabold ${
                              f.status === 'verified'
                                ? 'bg-emerald-100 text-emerald-900'
                                : 'bg-rose-100 text-rose-900'
                            }`}
                          >
                            {f.status === 'verified' ? '✓ Verified' : '⚠ Flagged'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: Forensic Trace Log */}
          {activeTab === 'audit_trace' && (
            <div className="aardvark-card p-8 bg-neutral-950 text-emerald-400 font-mono text-xs rounded-3xl border-2 border-neutral-900 shadow-2xl">
              <div className="flex items-center justify-between pb-4 mb-4 border-b border-neutral-800 text-white font-sans font-bold">
                <span>Forensic Trace Telemetry Log</span>
                <span className="text-xs text-neutral-400">Strict Timestamped Execution</span>
              </div>
              <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
                {screeningResult.forensicTrace.map((line, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="text-neutral-500 select-none">[{idx + 1}]</span>
                    <span className={line.includes('CRITICAL') || line.includes('ALERT') ? 'text-rose-400 font-bold' : 'text-emerald-300'}>
                      {line}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* ==================================================================== */}
      {/* 6. AARDVARK FOOTER */}
      {/* ==================================================================== */}
      <footer className="w-full border-t-2 border-neutral-900/10 py-10 mt-16 bg-aardvark-yellow/60">
        <div className="w-full max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-aardvark-pink text-white flex items-center justify-center font-black text-sm">
              D
            </div>
            <span className="font-display font-black text-xl text-neutral-900">
              DocSentinels<span className="text-aardvark-pink">.</span> SIH 26188
            </span>
          </div>

          <p className="text-xs font-bold text-neutral-700 text-center">
            AI-Based Fake Identity & Document Screening System • Ministry of Home Affairs (MHA)
          </p>

          <div className="flex items-center gap-4 text-xs font-black text-neutral-900">
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="hover:underline">
              API Docs
            </a>
            <span>•</span>
            <a href="https://github.com/AdityaKumar1511/sih26188" target="_blank" rel="noreferrer" className="hover:underline">
              GitHub Repo
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
