/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          950: '#050505', // Deep pitch black
          900: '#0A0A0A', // Main black background
          850: '#121212', // Surface dark black
          800: '#1C1C1C', // Card matte background
          700: '#2A2A2A', // Border gray
          600: '#383838', // Subtle line gray
          500: '#525252',
        },
        orange: {
          400: '#FB923C',
          500: '#F97316', // Solid Primary Orange
          600: '#EA580C', // Brand Primary Action
          700: '#C2410C',
          900: '#7C2D12', // Deep Orange Surface
          950: '#431407',
        },
        emerald: {
          400: '#4ADE80',
          500: '#22C55E',
          900: '#14532D',
          950: '#052E16',
        },
        red: {
          400: '#F87171',
          500: '#EF4444',
          900: '#7F1D1D',
          950: '#450A0A',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
};
