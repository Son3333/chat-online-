/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        telegram: {
          primary: '#2481cc',
          primaryHover: '#1d73b8',
          sidebarBgLight: '#ffffff',
          sidebarBgDark: '#17212b',
          chatBgLight: '#eef2f5',
          chatBgDark: '#0e1621',
          headerBgLight: '#ffffff',
          headerBgDark: '#17212b',
          cardLight: '#ffffff',
          cardDark: '#1e2c3a',
          bubbleSelfLight: '#effdde',
          bubbleSelfDark: '#2b5278',
          bubblePartnerLight: '#ffffff',
          bubblePartnerDark: '#182533',
        }
      }
    },
  },
  plugins: [],
};

