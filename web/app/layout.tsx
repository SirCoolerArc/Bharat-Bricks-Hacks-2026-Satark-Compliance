import type { Metadata } from "next";
import TopNav from "@/components/TopNav";
import "./globals.css";

export const metadata: Metadata = {
  title: "SATARK — UPI Fraud Protection",
  description:
    "Real-time UPI fraud detection and protection powered by Databricks intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <TopNav />
        <main className="page-container">{children}</main>
      </body>
    </html>
  );
}
