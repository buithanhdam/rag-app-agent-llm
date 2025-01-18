import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import NavBarComponent from '@/components/core/NavBarComponent';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'RAG Chat App',
  description: 'AI-powered chat and document processing system',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <NavBarComponent />
        <main className="pt-16">
          {children}
        </main>
      </body>
    </html>
  );
}