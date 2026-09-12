'use client';

import React from 'react';
import {
  ShieldCheck,
  Lock,
  Boxes,
  ExternalLink,
  Cpu,
  Fingerprint,
  FileCheck2,
  Database,
  ArrowUpRight,
  Sparkles
} from 'lucide-react';
import { ScrollReveal } from './ScrollReveal';

interface FooterProps {
  onOpenLedger: () => void;
  onNewScan: () => void;
}

export default function Footer({ onOpenLedger, onNewScan }: FooterProps) {
  return (
    <footer className="w-full border-t border-white/[0.06] bg-[#0A0E14] text-[#8B94A3] transition-all">
      <ScrollReveal direction="up" delay={0.1} distance={25}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12">
          
          {/* Main 4-Column Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-10 lg:gap-8 pb-12 border-b border-white/[0.06]">
            
            {/* Column 1: Brand & Terminal Info (Span 4) */}
            <div className="lg:col-span-4 space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-[#FFB454] flex items-center justify-center text-[#0A0E14] border border-[#FFB454]">
                  <ShieldCheck className="w-5 h-5 stroke-[2.2]" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-display font-black text-base tracking-tight uppercase text-[#F1F3F5]">
                      SENTINEL PROTOCOL
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#FFB454]/10 text-[#FFB454] border border-[#FFB454]/25">
                      v2.6.4-prod
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-[#8B94A3] block">
                    Ministry of Home Affairs | PS26188
                  </span>
                </div>
              </div>

              <p className="text-xs text-[#8B94A3] leading-relaxed max-w-sm">
                Next-generation multimodal document & biometric forensic screening terminal engineered for national border checkpoints, airports, and immigration e-gates.
              </p>

              {/* Status Chips */}
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/25 text-[10px] font-mono text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-sm bg-emerald-400 animate-pulse" />
                  <span>Polygon Amoy Active</span>
                </div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white/[0.04] border border-white/[0.08] text-[10px] font-mono text-[#F1F3F5]">
                  <Lock className="w-3 h-3 text-[#FFB454]" />
                  <span>Zero-PII Storage</span>
                </div>
              </div>
            </div>

            {/* Column 2: System Capabilities (Span 3) */}
            <div className="lg:col-span-3 space-y-3">
              <div className="text-xs font-display font-bold uppercase tracking-wider text-[#F1F3F5]">
                Forensic Pipeline
              </div>
              <ul className="space-y-2.5 text-xs">
                <li className="flex items-center gap-2 hover:text-[#FFB454] transition-colors cursor-default">
                  <Cpu className="w-3.5 h-3.5 text-[#FFB454]" />
                  <span>Error Level Analysis (ELA)</span>
                </li>
                <li className="flex items-center gap-2 hover:text-[#FFB454] transition-colors cursor-default">
                  <Fingerprint className="w-3.5 h-3.5 text-[#FFB454]" />
                  <span>SFace Neural 1:1 Biometrics</span>
                </li>
                <li className="flex items-center gap-2 hover:text-[#FFB454] transition-colors cursor-default">
                  <FileCheck2 className="w-3.5 h-3.5 text-[#FFB454]" />
                  <span>OCR & Checksum Integrity</span>
                </li>
                <li className="flex items-center gap-2 hover:text-[#FFB454] transition-colors cursor-default">
                  <Boxes className="w-3.5 h-3.5 text-[#FFB454]" />
                  <span>Merkle Hash-Chain Anchoring</span>
                </li>
              </ul>
            </div>

            {/* Column 3: Terminal Controls (Span 2) */}
            <div className="lg:col-span-2 space-y-3">
              <div className="text-xs font-display font-bold uppercase tracking-wider text-[#F1F3F5]">
                Terminal Navigation
              </div>
              <ul className="space-y-2 text-xs">
                <li>
                  <button
                    type="button"
                    onClick={() => {
                      onNewScan();
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                    className="hover:text-[#FFB454] transition-colors cursor-pointer text-left"
                  >
                    Screening Terminal
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={onOpenLedger}
                    className="hover:text-[#FFB454] transition-colors cursor-pointer text-left flex items-center gap-1"
                  >
                    <span>Audit Ledger</span>
                    <ArrowUpRight className="w-3 h-3 text-[#FFB454]" />
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => {
                      const el = document.getElementById('how-it-works');
                      if (el) el.scrollIntoView({ behavior: 'smooth' });
                    }}
                    className="hover:text-[#FFB454] transition-colors cursor-pointer text-left"
                  >
                    Workflow Guide
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => {
                      const el = document.getElementById('detection-capabilities');
                      if (el) el.scrollIntoView({ behavior: 'smooth' });
                    }}
                    className="hover:text-[#FFB454] transition-colors cursor-pointer text-left"
                  >
                    Defense Matrix
                  </button>
                </li>
              </ul>
            </div>

            {/* Column 4: Compliance & Legal (Span 3) */}
            <div className="lg:col-span-3 space-y-3">
              <div className="text-xs font-display font-bold uppercase tracking-wider text-[#F1F3F5]">
                Regulatory Compliance
              </div>
              <p className="text-[11px] text-[#8B94A3] leading-relaxed">
                Operates strictly under India's Digital Personal Data Protection (DPDP) Act 2023. Biometric templates are processed transiently in volatile memory; only cryptographic hash receipts are sealed to the ledger.
              </p>
              <div className="p-3 rounded-md bg-[#12161F] border border-white/[0.08] text-[11px] font-mono space-y-1">
                <div className="text-[#FFB454] font-semibold flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>ISO/IEC 30107-3 Biometric Liveness</span>
                </div>
                <div className="text-[#8B94A3] text-[10px]">
                  FIDO Alliance & ICAO 9303 Compliant Architecture
                </div>
              </div>
            </div>

          </div>

          {/* Bottom Bar */}
          <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono">
            <div className="flex items-center gap-3 text-[#8B94A3]">
              <span>© 2026 Sentinel Protocol. Ministry of Home Affairs (MHA).</span>
              <span className="hidden md:inline text-white/20">•</span>
              <span className="hidden md:inline text-[#8B94A3]">Smart India Hackathon PS26188</span>
            </div>

            <div className="flex items-center gap-4 text-[#8B94A3]">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-sm bg-emerald-400" />
                <span>Node 01: Operational</span>
              </span>
              <span className="text-white/20">•</span>
              <button
                type="button"
                onClick={onOpenLedger}
                className="text-[#FFB454] hover:text-[#FF8A3D] transition-colors underline-offset-4 hover:underline cursor-pointer flex items-center gap-1"
              >
                <span>Ledger Explorer</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>
          </div>

        </div>
      </ScrollReveal>
    </footer>
  );
}
