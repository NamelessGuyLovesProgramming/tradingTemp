/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../**/*.{html,js,py}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#121212',
        card: '#1E1E1E',
        text: '#E0E0E0',
        primary: '#3B82F6',
        secondary: '#6B7280',
        success: '#10B981',
        danger: '#EF4444',
        warning: '#F59E0B',
        grid: 'rgba(255, 255, 255, 0.1)',
      },
      boxShadow: {
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.25)',
      },
      borderRadius: {
        'xl': '0.75rem',
      },
    },
  },
  plugins: [],
}
