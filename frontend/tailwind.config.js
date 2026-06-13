/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        accent: {
          warm: '#FF6B35',
          'warm-dark': '#E55A2B',
          cool: '#00D4FF',
          'cool-dark': '#00B8D4',
        },
        // 海洋主题色阶（从 Pexels ocean-bg.jpg 提取）
        ocean: {
          50: '#FFFFFF',
          100: '#FFFFFF',
          200: '#FFFFFF',
          300: '#FFFFFF',
          400: '#D7F4FF',
          500: '#A5BFE2',
          600: '#91A8C6',
          700: '#7D91AB',
          800: '#697A90',
          900: '#556375',
        },
        // 极光主题色阶（从 Pexels aurora-bg.jpg 提取）
        aurora: {
          50: '#9ABED5',
          100: '#8AACC2',
          200: '#6A8A9E',
          300: '#4A6779',
          400: '#2A4455',
          500: '#0B2231',
          600: '#091D2B',
          700: '#081925',
          800: '#07151F',
          900: '#051119',
        },
        surface: {
          dark: 'rgba(0, 0, 0, 0.5)',
          light: 'rgba(255, 255, 255, 0.85)',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system', 'BlinkMacSystemFont',
          'SF Pro Text', 'Helvetica Neue',
          'Arial', 'sans-serif',
        ],
        display: [
          '-apple-system', 'BlinkMacSystemFont',
          'SF Pro Display', 'Helvetica Neue',
          'Arial', 'sans-serif',
        ],
      },
      borderRadius: {
        DEFAULT: '8px',
      },
      fontSize: {
        hero: ['48px', { lineHeight: '1.1', fontWeight: '600' }],
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
