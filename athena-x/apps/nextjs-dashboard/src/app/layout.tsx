import type { Metadata } from 'next';
import { GeistSans } from 'geist/font/sans';
import { GeistMono } from 'geist/font/mono';
import './globals.css';

export const metadata: Metadata = {
    title: 'ATHENA-X — Quantitative Intelligence Terminal',
    description: 'Institutional-grade quantitative market intelligence terminal.',
    authors: [{ name: 'ATHENA-X' }],
    keywords: ['ATHENA-X', 'quantitative', 'market intelligence', 'trading terminal'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en" className={`dark ${GeistSans.variable} ${GeistMono.variable}`} suppressHydrationWarning>
            <body className="font-sans">
                {children}
            </body>
        </html>
    );
}
