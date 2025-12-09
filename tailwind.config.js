/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./*.html"], // Surveille tes fichiers HTML
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#4A6C6F',
          accent: '#C66B3D',
          dark: '#2D2A26',
          light: '#F3E5AB',
          bg: '#FAFAF9'
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        serif: ['Playfair Display', 'serif'],
      }
    },
  },
  plugins: [],
}
