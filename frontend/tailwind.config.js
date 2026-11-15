/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        museum: {
          bg: '#f5f0eb',
          text: '#2c2c2c',
          accent: '#8b6914',
          light: '#ede8e0',
          border: '#d4c9b8',
          muted: '#7a7267',
        },
      },
      fontFamily: {
        display: ['Georgia', 'serif'],
        body: ['system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
