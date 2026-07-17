import type { Config } from 'tailwindcss';

const config: Config = {
    darkMode: 'class',  // forced dark — Change 8 of STEP 2.1
    content: [
        './src/**/*.{ts,tsx}',
        '../../packages/ui-kit/src/**/*.{ts,tsx}',
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['var(--font-geist-sans)', 'system-ui', 'sans-serif'],
                mono: ['var(--font-geist-mono)', 'monospace'],
            },
            colors: {
                background: 'rgb(var(--background) / <alpha-value>)',
                foreground: 'rgb(var(--foreground) / <alpha-value>)',
                card: 'rgb(var(--card) / <alpha-value>)',
                muted: 'rgb(var(--muted) / <alpha-value>)',
                border: 'rgb(var(--border) / <alpha-value>)',
                primary: 'rgb(var(--primary) / <alpha-value>)',
                pos: 'rgb(var(--pos) / <alpha-value>)',
                neg: 'rgb(var(--neg) / <alpha-value>)',
                accent: 'rgb(var(--accent) / <alpha-value>)',
                sidebar: 'rgb(var(--sidebar) / <alpha-value>)',
            },
            animation: {
                'ticker': 'ticker-scroll 40s linear infinite',
                'pulse-dot': 'pulse-dot 1.6s ease-in-out infinite',
            },
        },
    },
    plugins: [require('tailwindcss-animate')],
};

export default config;
