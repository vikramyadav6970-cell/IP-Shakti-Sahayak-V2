/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border, 214.3 31.8% 91.4%))",
        input: "hsl(var(--input, 214.3 31.8% 91.4%))",
        ring: "hsl(var(--ring, 168 80% 23%))",
        background: "hsl(var(--background, 0 0% 100%))",
        foreground: "hsl(var(--foreground, 222.2 84% 4.9%))",
        primary: {
          DEFAULT: "hsl(var(--primary, 168 80% 23%))",
          foreground: "hsl(var(--primary-foreground, 210 40% 98%))",
        },
        ayush: {
          50: "#f0fdf4",
          100: "#dcfce7",
          500: "#22c55e",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
        },
        statute: {
          50: "#f8fafc",
          100: "#f1f5f9",
          600: "#475569",
          800: "#1e293b",
          900: "#0f172a",
        },
      },
    },
  },
  plugins: [],
};
