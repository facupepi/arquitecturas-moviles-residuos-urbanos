// Paleta y medidas del diseño del TP5 (San Francisco Conecta) aplicadas sobre las clases de Tailwind.
// Se compila con `npm run estilos` (ver app/package.json).
module.exports = Object.assign({ content: ['../app/index.html'] }, {
      theme: {
        extend: {
          fontFamily: { sans: ['Quicksand', 'system-ui', 'Arial', 'sans-serif'] },
          colors: {
            slate:   { 50: '#f7f9fb', 100: '#f4f7fa', 200: '#dce4eb', 300: '#b7c8d6', 400: '#8a9bad', 500: '#5f7083', 600: '#526174', 700: '#3a4859', 800: '#1e2939', 900: '#102b3d', 950: '#0b1f2d' },
            sky:     { 50: '#f0f9fe', 100: '#e0f2fc', 200: '#bfe4f7', 300: '#8dd0f0', 400: '#4db7e9', 500: '#009ee2', 600: '#0089c7', 700: '#0077ae', 800: '#005c88', 900: '#00476a', 950: '#00334d' },
            blue:    { 50: '#f0f9fe', 100: '#e0f2fc', 200: '#bfe4f7', 300: '#8dd0f0', 400: '#4db7e9', 500: '#009ee2', 600: '#0089c7', 700: '#0077ae', 800: '#005c88', 900: '#00476a' },
            emerald: { 50: '#f4f9ef', 100: '#edf5e6', 200: '#d4e8c4', 300: '#b5d897', 400: '#8bbf5e', 500: '#6aa435', 600: '#528429', 700: '#3c6520', 800: '#2f5019', 900: '#244013', 950: '#1a2f0e' },
            teal:    { 50: '#f4f9ef', 100: '#edf5e6', 200: '#d4e8c4', 300: '#b5d897', 400: '#8bbf5e', 500: '#6aa435', 600: '#528429', 700: '#3c6520', 800: '#2f5019', 900: '#244013', 950: '#1a2f0e' },
            orange:  { 50: '#fff8ee', 100: '#fff1df', 200: '#fddcb0', 300: '#fbc07a', 400: '#f79a3a', 500: '#f07e07', 600: '#c96300', 700: '#a84f00', 800: '#833d00', 900: '#5f2c00' },
            amber:   { 50: '#fffbe6', 100: '#fff6cd', 200: '#ffec9a', 300: '#fbdb5c', 400: '#f4c000', 500: '#d9a800', 600: '#a98400', 700: '#7a5e00', 800: '#5e4800', 900: '#453500', 950: '#2e2400' },
            rose:    { 50: '#fef3f5', 100: '#fde6ea', 200: '#f9c5cf', 300: '#f29aab', 400: '#e0476a', 500: '#ce0e3c', 600: '#b80e37', 700: '#a21937', 800: '#7e1329', 900: '#5c0e1f' },
            brand:   { 50: '#f0f9fe', 100: '#e0f2fc', 500: '#009ee2', 600: '#0089c7', 700: '#0077ae', 800: '#005c88', 900: '#0077ae', 950: '#00476a' },
            muni:    { 50: '#f0f9fe', 600: '#0089c7', 700: '#0077ae', 800: '#005c88', 900: '#00476a' }
          },
          fontSize: { xs: ['14px', '20px'], sm: ['15px', '22px'], base: ['16px', '24px'], lg: ['18px', '26px'], xl: ['20px', '28px'], '2xl': ['22px', '30px'], '3xl': ['28px', '34px'] },
          borderRadius: { lg: '10px', xl: '12px', '2xl': '18px', '3xl': '22px' },
          boxShadow: {
            sm: '0 2px 10px rgba(30, 41, 57, 0.06)',
            DEFAULT: '0 2px 10px rgba(30, 41, 57, 0.08)',
            md: '0 2px 10px rgba(30, 41, 57, 0.10)',
            lg: '0 6px 24px rgba(16, 43, 61, 0.16)',
            xl: '0 6px 24px rgba(16, 43, 61, 0.20)',
            '2xl': '0 6px 24px rgba(16, 43, 61, 0.22)'
          }
        }
      }
    });
