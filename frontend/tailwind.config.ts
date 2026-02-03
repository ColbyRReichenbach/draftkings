import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', '"IBM Plex Sans"', 'sans-serif'],
        body: ['"IBM Plex Sans"', '"Space Grotesk"', 'sans-serif']
      }
    }
  },
  plugins: []
} satisfies Config;
