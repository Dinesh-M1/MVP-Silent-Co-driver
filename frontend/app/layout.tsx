import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Silent Co-Driver',
  description: 'AI-powered racing co-driver dashboard',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
