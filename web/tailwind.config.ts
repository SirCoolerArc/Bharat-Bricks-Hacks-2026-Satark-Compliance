import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // SATARK neutral palette — calm, trust-building
        surface: {
          50: "#FAFAFA",
          100: "#F5F5F5",
          200: "#EEEEEE",
          300: "#E0E0E0",
          400: "#BDBDBD",
        },
        ink: {
          DEFAULT: "#212121",
          muted: "#757575",
          faint: "#9E9E9E",
        },
        accent: {
          DEFAULT: "#1A73E8",
          light: "#E8F0FE",
        },
        risk: {
          low: "#34A853",
          medium: "#F9AB00",
          high: "#EA4335",
          critical: "#B31412",
        },
      },
      borderWidth: {
        thin: "0.5px",
      },
      fontFamily: {
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
