import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        sidebar: "#0F1117",
        page: "#F4F3EF",
        card: "#FFFFFF",
        border: "#E5E4DE",
        "text-primary": "#1C1C1A",
        "text-secondary": "#6B7280",
        "text-muted": "#9CA3AF",
        "risk-high": "#DC2626",
        "risk-high-bg": "#FEF2F2",
        "risk-med": "#D97706",
        "risk-med-bg": "#FFFBEB",
        "risk-low": "#16A34A",
        "risk-low-bg": "#F0FDF4",
        "nav-active": "#1D6FA5",
        "nav-active-bg": "#EBF5FF",
        "chat-bot": "#F3F4F6",
        "chat-user": "#EBF5FF",
      },
      fontSize: {
        "kpi": ["28px", { lineHeight: "1.2", fontWeight: "600", letterSpacing: "-0.02em" }],
        "body": ["13px", { lineHeight: "1.5" }],
        "label": ["11px", { lineHeight: "1.4", letterSpacing: "0.05em" }],
      },
      boxShadow: {
        "soft": "0 4px 20px -2px rgba(0, 0, 0, 0.04), 0 0 3px rgba(0,0,0,0.02)",
        "hover": "0 8px 30px -4px rgba(0, 0, 0, 0.08), 0 0 5px rgba(0,0,0,0.03)",
        "card": "0 2px 10px -1px rgba(0, 0, 0, 0.02), 0 1px 3px -1px rgba(0,0,0,0.04)",
      },
      animation: {
        "pulse-live": "pulse-live 2s ease-in-out infinite",
        "bounce-dot": "bounce-dot 1.4s ease-in-out infinite",
      },
      keyframes: {
        "pulse-live": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        "bounce-dot": {
          "0%, 80%, 100%": { transform: "scale(0)" },
          "40%": { transform: "scale(1)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
