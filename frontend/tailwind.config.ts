import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'dk-green': '#53B848',
        'dk-black': '#0B0B0B',
        'dk-surface': '#121212',
        'dk-border': '#2A2A2A',
        'dk-red': '#DC2626',   // Critical
        'dk-orange': '#F3701B', // High
        'dk-yellow': '#FFB81C', // Medium
      },
      fontFamily: {
        display: ['"Oswald"', '"Roboto Condensed"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      backgroundImage: {
        'grid-pattern': `linear-gradient(to right, #2A2A2A 1px, transparent 1px),
                         linear-gradient(to bottom, #2A2A2A 1px, transparent 1px)`,
      },
      letterSpacing: {
        'tighter-custom': '-0.05em',
        'widest-custom': '0.15em',
      },
      borderRadius: {
        'sm-custom': '2px', // Sharper corners for a technical feel
      },
    }
  },
  plugins: []
} satisfies Config;
