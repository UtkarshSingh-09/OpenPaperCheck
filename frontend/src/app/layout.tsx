import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

const inter = Inter({
  variable: '--font-sans',
  subsets: ['latin'],
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-mono',
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'OpenPaperCheck — Scholarly Retraction & Reference Integrity Checker',
  description:
    'Paste a paper DOI to inspect whether it has been retracted or cites retracted literature using Retraction Watch and Crossref open data.',
  keywords: [
    'retraction',
    'retraction watch',
    'crossref',
    'academic integrity',
    'scholarly publishing',
    'DOI checker',
    'peer review',
  ],
  authors: [{ name: 'OpenPaperCheck Contributors' }],
  openGraph: {
    title: 'OpenPaperCheck — Scholarly Retraction & Reference Integrity Checker',
    description:
      'Fast, honest academic paper retraction facts with zero subjective accusations.',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
