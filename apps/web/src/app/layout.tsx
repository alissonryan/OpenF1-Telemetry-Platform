import type { Metadata } from 'next';
import { Barlow_Condensed, Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains',
  display: 'swap',
});

const barlowCondensed = Barlow_Condensed({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
  weight: ['400', '500', '600', '700'],
});

export const metadata: Metadata = {
  title: 'F1 Telemetry Platform',
  description: 'Real-time F1 telemetry dashboard and ML-powered predictions',
  keywords: ['F1', 'Formula 1', 'Telemetry', 'Dashboard', 'Predictions'],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} ${barlowCondensed.variable}`}
    >
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
