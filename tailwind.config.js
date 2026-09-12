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
          950: '#0A0E14', // Base near-black with graphite/blue tint
          900: '#12161F', // Subtle gradient secondary surface
          850: '#161B26', // Surface dark graphite
          800: '#1E2536', // Card matte background
          700: '#2A344A', // Border subtle
          600: '#3D4A66', // Line muted
          500: '#8B94A3', // Muted text
        },
        accent: {
          DEFAULT: '#FFB454', // Warm amber primary accent
          hover: '#FF8A3D',   // Deeper warm amber for hover/pressed
          glow: 'rgba(255, 180, 84, 0.25)',
        },
        amber: {
          400: '#FFC875',
          500: '#FFB454',
          600: '#FF8A3D',
          700: '#E06B22',
          900: '#66320D',
          950: '#331704',
        },
        orange: {
          400: '#FFC875',
          500: '#FFB454', // Primary Warm Amber alias
          600: '#FF8A3D', // Hover Warm Amber alias
          700: '#E06B22',
          900: '#66320D',
          950: '#331704',
        },
        emerald: {
          400: '#34D399', // Success emerald
          500: '#10B981',
          900: '#064E3B',
          950: '#022C22',
        },
        danger: {
          DEFAULT: '#EF4444',
          dark: '#DC2626',
        },
        red: {
          400: '#F87171',
          500: '#EF4444',
          600: '#DC2626',
          900: '#7F1D1D',
          950: '#450A0A',
        },
        heading: '#F1F3F5',
        muted: '#8B94A3',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'glow-danger': '0 1px 3px rgba(0, 0, 0, 0.3)',
        'glow-accent': '0 1px 3px rgba(0, 0, 0, 0.3)',
        'glass-card': '0 4px 12px 0 rgba(0, 0, 0, 0.3)',
      },
      borderRadius: {
        'card': '8px',
      },
    },
  },
  plugins: [],
};
