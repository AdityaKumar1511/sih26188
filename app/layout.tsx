import type { Metadata } from 'next';
import './globals.css';
import CustomCursor from './components/CustomCursor';

export const metadata: Metadata = {
  title: 'Sentinel — AI Document & Identity Screening | MHA PS26188',
  description: 'AI-powered fake identity & document screening system with live biometric verification. Ministry of Home Affairs — Smart India Hackathon 2026.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen">
        <CustomCursor />
        {children}
      </body>
    </html>
  );
}
