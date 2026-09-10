'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scan,
  ShieldCheck,
  Boxes,
  Lock,
  Menu,
  X,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Fingerprint
} from 'lucide-react';

interface NavbarProps {
  appState: 'upload' | 'processing' | 'results';
  onNewScan: () => void;
  onOpenLedger: () => void;
  onNavigateTab?: (tab: string) => void;
  hasResult?: boolean;
}

export default function Navbar({
  appState,
  onNewScan,
  onOpenLedger,
  onNavigateTab,
  hasResult = false,
}: NavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    {
      label: 'TERMINAL',
      action: () => {
        onNewScan();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      },
    },
    {
      label: 'FORENSICS',
      action: () => {
        if (hasResult && onNavigateTab) {
          onNavigateTab('fields');
        } else {
          window.scrollTo({ top: 400, behavior: 'smooth' });
        }
      },
    },
    {
      label: 'BIOMETRICS',
      action: () => {
        if (hasResult && onNavigateTab) {
          onNavigateTab('biometrics');
        } else {
          window.scrollTo({ top: 400, behavior: 'smooth' });
        }
      },
    },
    {
      label: 'AUDIT LEDGER',
      action: onOpenLedger,
    },
    {
      label: 'COMPLIANCE',
      action: () => {
        const footerEl = document.querySelector('footer');
        if (footerEl) footerEl.scrollIntoView({ behavior: 'smooth' });
      },
    },
  ];

  return (
    <header className="sticky top-0 z-50 w-full transition-all border-b border-white/[0.05]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        
        {/* ================================================================== */}
        {/* LEFT: Logo + Stacked Wordmark (matching reference design style)     */}
        {/* ================================================================== */}
        <div
          onClick={() => {
            onNewScan();
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
          className="flex items-center gap-3.5 cursor-pointer select-none group"
        >
          {/* Glowing Icon Badge */}
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-[#FFB454] to-[#FF8A3D] flex items-center justify-center text-[#0A0E14] shadow-[0_0_24px_rgba(255,180,84,0.3)] ring-1 ring-white/20 group-hover:scale-105 group-hover:shadow-[0_0_32px_rgba(255,180,84,0.5)] transition-all duration-300">
            <Scan className="w-5 h-5 stroke-[2.4]" />
          </div>

          {/* Stacked Wordmark (inspired by DON'T BOARD ME stacked typography) */}
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-display font-black text-lg tracking-tight uppercase leading-[0.95] text-[#F1F3F5] group-hover:text-white transition-colors">
                SENTINEL
              </span>
              <span className="text-[10px] font-mono font-bold text-[#FFB454] bg-[#FFB454]/10 border border-[#FFB454]/25 px-1.5 py-0.2 rounded-md tracking-tight">
                MHA
              </span>
            </div>
            <span className="text-[10px] font-display font-bold uppercase tracking-[0.2em] text-[#8B94A3] mt-0.5 leading-none">
              PROTOCOL
            </span>
          </div>
        </div>

        {/* ================================================================== */}
        {/* CENTER: Navigation Links (Clean uppercase typography)               */}
        {/* ================================================================== */}
        <nav className="hidden md:flex items-center gap-7 lg:gap-9">
          {navLinks.map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={item.action}
              className="text-xs font-display font-bold uppercase tracking-[0.14em] text-[#8B94A3] hover:text-[#FFB454] transition-colors cursor-pointer py-1 relative group"
            >
              <span>{item.label}</span>
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gradient-to-r from-[#FFB454] to-[#FF8A3D] group-hover:w-full transition-all duration-300 rounded-full" />
            </button>
          ))}
        </nav>

        {/* ================================================================== */}
        {/* RIGHT: Status Indicator + Master Action CTA (matching ref button)   */}
        {/* ================================================================== */}
        <div className="hidden sm:flex items-center gap-4">
          
          {/* Live Node Status Pill */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.08] text-[11px] font-mono text-[#8B94A3]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-[#8B94A3]">Amoy EVM</span>
          </div>

          {/* Master CTA Button (prominent tab-style action button like BOOK NOW) */}
          {appState === 'results' ? (
            <button
              type="button"
              onClick={onNewScan}
              className="px-6 py-2.5 rounded-full bg-gradient-to-r from-[#FFB454] to-[#FF8A3D] hover:from-[#FF8A3D] hover:to-[#FF7A20] text-[#0A0E14] font-display font-bold text-xs uppercase tracking-wider flex items-center gap-2 shadow-[0_0_24px_rgba(255,180,84,0.35)] hover:shadow-[0_0_32px_rgba(255,180,84,0.55)] transition-all duration-200 cursor-pointer hover:scale-[1.03] active:scale-[0.98]"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Next Passenger</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                onNewScan();
                window.scrollTo({ top: 300, behavior: 'smooth' });
              }}
              className="px-6 py-2.5 rounded-full bg-gradient-to-r from-[#FFB454] to-[#FF8A3D] hover:from-[#FF8A3D] hover:to-[#FF7A20] text-[#0A0E14] font-display font-bold text-xs uppercase tracking-wider flex items-center gap-2 shadow-[0_0_24px_rgba(255,180,84,0.35)] hover:shadow-[0_0_32px_rgba(255,180,84,0.55)] transition-all duration-200 cursor-pointer hover:scale-[1.03] active:scale-[0.98]"
            >
              <Scan className="w-3.5 h-3.5" />
              <span>Start Screening</span>
            </button>
          )}

        </div>

        {/* Mobile Hamburger Button */}
        <div className="flex md:hidden items-center gap-2">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-xl bg-white/[0.04] border border-white/10 text-[#F1F3F5] hover:text-[#FFB454] transition cursor-pointer"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

      </div>

      {/* Mobile Navigation Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="md:hidden border-t border-white/[0.08] bg-[#0A0E14] px-4 py-5 space-y-4"
          >
            <div className="flex flex-col space-y-3">
              {navLinks.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    item.action();
                    setMobileMenuOpen(false);
                  }}
                  className="flex items-center justify-between py-2 text-sm font-display font-bold uppercase tracking-wider text-[#8B94A3] hover:text-[#FFB454] transition text-left"
                >
                  <span>{item.label}</span>
                  <ChevronRight className="w-4 h-4 text-[#8B94A3]" />
                </button>
              ))}
            </div>

            <div className="pt-3 border-t border-white/[0.08] flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-mono text-[#8B94A3]">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>Amoy EVM Active</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  onOpenLedger();
                  setMobileMenuOpen(false);
                }}
                className="px-4 py-2 rounded-full bg-[#FFB454]/10 border border-[#FFB454]/30 text-[#FFB454] text-xs font-mono font-bold"
              >
                Ledger
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
