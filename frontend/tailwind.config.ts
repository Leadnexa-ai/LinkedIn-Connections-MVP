import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#f5f7fb",
        ink: "#111827",
        muted: "#6b7280",
        brand: "#2563eb",
        panel: "#ffffff",
        border: "#e5e7eb",
        success: "#16a34a",
        warning: "#d97706"
      },
      boxShadow: {
        panel: "0 10px 30px rgba(15, 23, 42, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
