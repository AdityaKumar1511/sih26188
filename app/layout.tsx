import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'MHA AI Document & Identity Screening System | PS26188',
  description: 'AI-Based Fake Identity & Document Screening System developed for Ministry of Home Affairs (MHA) - Smart India Hackathon',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className="bg-security-950 text-slate-100 min-h-screen selection:bg-cyan-500/30 selection:text-cyan-200">
        {children}
      </body>
    </html>
  );
}
