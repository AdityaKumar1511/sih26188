'use client';

import React from 'react';
import {
  Scan,
  ShieldAlert,
  ShieldCheck,
  Cpu,
  Fingerprint,
  FileCheck,
  Boxes,
  Lock,
  Zap,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Layers,
  FileText,
  Camera
} from 'lucide-react';
import { ScrollReveal, StaggerContainer, StaggerItem } from './ScrollReveal';

export default function HomeSections() {
  const steps = [
    {
      number: '01',
      title: 'Multimodal Document Intake',
      subtitle: 'Optical & Tamper Analysis',
      description:
        'Analyzes physical and digital documents using Error Level Analysis (ELA) to expose recompression artifacts, font discrepancies, and photo substitution.',
      tags: ['ELA Compression', 'OCR Extraction', 'Hologram Check'],
      icon: FileText,
      accent: 'from-[#FFB454] to-[#FF8A3D]',
    },
    {
      number: '02',
      title: 'SFace Neural Biometrics',
      subtitle: '1:1 Live Facial Comparison',
      description:
        'Extracts 128-dimensional facial embedding vectors from ID portraits and compares with live camera feeds via cosine similarity metric with anti-spoof checks.',
      tags: ['Cosine Metric', '3D Texture Liveness', 'Anti-Spoof'],
      icon: Fingerprint,
      accent: 'from-emerald-400 to-teal-500',
    },
    {
      number: '03',
      title: 'EVM Ledger Anchoring',
      subtitle: 'Cryptographic Non-Repudiation',
      description:
        'Generates a SHA-256 Merkle verdict digest sealed on-chain to Polygon PoS. Guarantees tamper-evident audit logs while maintaining complete citizen privacy.',
      tags: ['Zero-PII Storage', 'Merkle Root', 'Polygon PoS'],
      icon: Boxes,
      accent: 'from-[#FFB454] to-[#FF8A3D]',
    },
  ];

  const capabilities = [
    {
      title: 'Error Level Analysis (ELA)',
      category: 'FORENSIC VISION',
      description:
        'Reveals digital photo swaps and spliced text by identifying localized differences in compression levels across document surfaces.',
      icon: Cpu,
    },
    {
      title: '1:1 SFace Neural Embedding',
      category: 'BIOMETRIC MATCHING',
      description:
        'Sub-second facial landmark alignment and feature extraction designed to match passengers reliably across aging, glasses, and terminal lighting.',
      icon: Fingerprint,
    },
    {
      title: 'Passive Liveness Telemetry',
      category: 'ANTI-SPOOFING DEFENSE',
      description:
        'Detects presentation attacks including 4K display replays, printed paper masks, and curved cardboard photo substitutions.',
      icon: ShieldCheck,
    },
    {
      title: 'Checksum & MRZ Verification',
      category: 'INTEGRITY AUDITING',
      description:
        'Mathematically verifies Verhoeff checksums on Aadhaar, PAN structure algorithms, and ICAO 9303 machine-readable travel passport zones.',
      icon: FileCheck,
    },
    {
      title: 'Zero-PII On-Chain Receipts',
      category: 'DATA PROTECTION',
      description:
        'Full compliance with India’s DPDP Act 2023. No names, photographs, or national ID numbers are ever uploaded or written to the blockchain ledger.',
      icon: Lock,
    },
    {
      title: 'Border Officer Triage Protocol',
      category: 'DECISION ASSURANCE',
      description:
        'Provides border inspection officers with instant secondary check referrals, automated risk scores, and court-admissible audit export.',
      icon: ShieldAlert,
    },
  ];

  const metrics = [
    { value: '< 450ms', label: 'Average Pipeline Latency', detail: 'Real-time inference at edge terminal' },
    { value: '99.4%', label: 'SFace Biometric Accuracy', detail: '0.40 cosine similarity threshold' },
    { value: '0 PII', label: 'Personal Data on Ledger', detail: 'Cryptographic SHA-256 digests only' },
    { value: '100%', label: 'Audit Trail Non-Repudiation', detail: 'Anchored on Polygon PoS blockchain' },
  ];

  return (
    <div className="space-y-24 pt-12">
      
      {/* ================================================================== */}
      {/* SECTION 1: HOW SENTINEL OPERATES (Pipeline Steps)                  */}
      {/* ================================================================== */}
      <section id="how-it-works" className="space-y-12">
        <ScrollReveal direction="up" delay={0.1}>
          <div className="text-center max-w-3xl mx-auto space-y-3 px-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-[11px] font-mono text-[#FFB454]">
              <Layers className="w-3.5 h-3.5" />
              <span className="uppercase tracking-widest font-semibold">MULTIMODAL PIPELINE</span>
            </div>
            <h3 className="text-2xl sm:text-4xl font-display font-bold text-[#F1F3F5] tracking-tight">
              How Sentinel Screens Passenger Credentials
            </h3>
            <p className="text-sm text-[#8B94A3] leading-relaxed">
              Every identity credential passes through a three-stage zero-trust verification architecture before granting entry clearance.
            </p>
          </div>
        </ScrollReveal>

        <StaggerContainer stagger={0.15} delay={0.2} className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <StaggerItem key={idx} direction="up" distance={30}>
                <div className="rounded-[20px] bg-white/[0.03] backdrop-blur-xl border border-white/[0.08] p-6 flex flex-col justify-between h-full space-y-6 hover:border-white/[0.18] hover:shadow-[0_16px_36px_rgba(0,0,0,0.5),0_0_24px_rgba(255,180,84,0.06)] transition-all duration-300 group">
                  <div className="space-y-4">
                    
                    {/* Header Row: Step Number & Icon */}
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-black text-2xl text-[#FFB454] tracking-tight">
                        {step.number}
                      </span>
                      <div className="w-10 h-10 rounded-xl bg-white/[0.05] border border-white/10 flex items-center justify-center text-[#FFB454] group-hover:scale-110 transition-transform">
                        <Icon className="w-5 h-5" />
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <div className="text-[11px] font-mono text-[#8B94A3] uppercase tracking-wider">
                        {step.subtitle}
                      </div>
                      <h4 className="text-lg font-display font-bold text-[#F1F3F5] tracking-tight">
                        {step.title}
                      </h4>
                    </div>

                    <p className="text-xs text-[#8B94A3] leading-relaxed">
                      {step.description}
                    </p>
                  </div>

                  {/* Tags */}
                  <div className="pt-4 border-t border-white/[0.06] flex flex-wrap gap-1.5">
                    {step.tags.map((tag, tIdx) => (
                      <span
                        key={tIdx}
                        className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.04] text-[#8B94A3] border border-white/[0.06]"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                </div>
              </StaggerItem>
            );
          })}
        </StaggerContainer>
      </section>

      {/* ================================================================== */}
      {/* SECTION 2: DETECTION CAPABILITIES (6-Grid Defense Matrix)         */}
      {/* ================================================================== */}
      <section id="detection-capabilities" className="space-y-12">
        <ScrollReveal direction="up" delay={0.1}>
          <div className="text-center max-w-3xl mx-auto space-y-3 px-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-[11px] font-mono text-[#FFB454]">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span className="uppercase tracking-widest font-semibold">SECURITY DEFENSE MATRIX</span>
            </div>
            <h3 className="text-2xl sm:text-4xl font-display font-bold text-[#F1F3F5] tracking-tight">
              Enterprise Forensic Detection Arsenal
            </h3>
            <p className="text-sm text-[#8B94A3] leading-relaxed">
              Multi-layered computer vision algorithms and cryptographic validation protocols guard national borders against sophisticated identity fraud.
            </p>
          </div>
        </ScrollReveal>

        <StaggerContainer stagger={0.08} delay={0.15} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {capabilities.map((cap, idx) => {
            const Icon = cap.icon;
            return (
              <StaggerItem key={idx} direction="up" distance={25}>
                <div className="rounded-[20px] bg-white/[0.03] backdrop-blur-xl border border-white/[0.08] p-5 space-y-3 hover:border-white/[0.16] hover:bg-white/[0.05] transition-all duration-300 h-full flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="w-9 h-9 rounded-xl bg-white/[0.04] border border-white/10 flex items-center justify-center text-[#FFB454]">
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className="text-[10px] font-mono text-[#8B94A3] tracking-wider uppercase">
                        {cap.category}
                      </span>
                    </div>

                    <h4 className="text-sm font-display font-bold text-[#F1F3F5]">
                      {cap.title}
                    </h4>

                    <p className="text-xs text-[#8B94A3] leading-relaxed">
                      {cap.description}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-white/[0.05] flex items-center gap-1.5 text-[11px] font-mono text-emerald-400">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Active Protocol</span>
                  </div>
                </div>
              </StaggerItem>
            );
          })}
        </StaggerContainer>
      </section>

      {/* ================================================================== */}
      {/* SECTION 3: OPERATIONAL TELEMETRY & STATS (Numbers Row)            */}
      {/* ================================================================== */}
      <section className="space-y-8">
        <ScrollReveal direction="up" delay={0.1}>
          <div className="rounded-[24px] bg-white/[0.03] backdrop-blur-xl border border-white/[0.08] p-8 lg:p-10 shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 divide-y lg:divide-y-0 lg:divide-x divide-white/[0.08]">
              {metrics.map((m, idx) => (
                <div key={idx} className={`space-y-1.5 ${idx > 0 ? 'pt-6 lg:pt-0 lg:pl-8' : ''}`}>
                  <div className="text-2xl sm:text-4xl font-mono font-black text-[#FFB454] tracking-tight">
                    {m.value}
                  </div>
                  <div className="text-xs font-display font-bold text-[#F1F3F5]">
                    {m.label}
                  </div>
                  <div className="text-[11px] text-[#8B94A3] font-mono">
                    {m.detail}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </ScrollReveal>
      </section>

    </div>
  );
}
