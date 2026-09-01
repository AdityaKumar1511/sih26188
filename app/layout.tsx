import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DocSentinels • AI Document Screening & Biometric Verification | MHA PS26188',
  description: 'DocSentinels: AI-Based Fake Identity & Document Screening System developed for Ministry of Home Affairs (MHA) - Smart India Hackathon',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=Syne:wght@700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-aardvark-yellow text-aardvark-black min-h-screen selection:bg-aardvark-pink selection:text-white font-sans antialiased overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}
