/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // Palette sampled from the "Session 5 — Document Intelligence" deck:
      // deep navy canvas, coral accent, teal/sky section labels, light surface.
      colors: {
        navy: "#0F2A43",
        coral: {
          DEFAULT: "#EF6A4F",
          dark: "#DD5639",
        },
        teal: {
          DEFAULT: "#2E7BA6",
          light: "#6FB0D0",
        },
        surface: "#EEF2F5",
      },
    },
  },
  plugins: [],
};
