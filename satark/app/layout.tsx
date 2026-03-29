import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";

export const metadata = {
  title: "SATARK — Fraud Compliance Dashboard",
  description:
    "Real-time UPI fraud monitoring and compliance dashboard for Indian banks and RBI oversight. Powered by ML-driven risk scoring across 150K+ transactions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-page">
        <Sidebar />
        <Topbar />
        <main className="ml-14 mt-12 min-h-[calc(100vh-48px)]">
          {children}
        </main>
      </body>
    </html>
  );
}
