import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand
        "brand-primary": "#1B4F72",
        "brand-primary-dark": "#153D5E",
        "brand-primary-light": "#2E6A9A",
        "brand-secondary": "#117A65",
        "brand-secondary-dark": "#0D5F4F",
        "brand-secondary-light": "#1A9A84",
        
        // Accent
        "accent-gold": "#D4AC0D",
        "accent-amber": "#E67E22",
        
        // Surfaces
        "surface-0": "#FFFFFF",
        "surface-1": "#F8FAFB",
        "surface-2": "#EEF2F7",
        
        // Text
        "text-primary": "#1A202C",
        "text-secondary": "#4A5568",
        "text-muted": "#718096",
        
        // Semantic
        success: "#27AE60",
        danger: "#C0392B",
        warning: "#F39C12",
        info: "#2980B9",
        
        // Map common colors
        primary: "#1B4F72",
        secondary: "#117A65",
      },
      fontFamily: {
        display: ["Playfair Display", "Georgia", "serif"],
        sans: ["DM Sans", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      borderRadius: {
        sm: "0.25rem",
        md: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
      },
      boxShadow: {
        sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        md: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
        lg: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
      },
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
      },
      minHeight: {
        "48px": "48px",
      },
      minWidth: {
        "48px": "48px",
      },
      animation: {
        in: "animateIn 0.3s ease-out",
      },
      keyframes: {
        animateIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;