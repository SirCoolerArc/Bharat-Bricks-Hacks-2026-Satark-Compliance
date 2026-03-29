"use client";

import KPIStrip from "@/components/dashboard/KPIStrip";
import AlertFeed from "@/components/dashboard/AlertFeed";
import ScamBreakdown from "@/components/dashboard/ScamBreakdown";
import HourlyHeatmap from "@/components/dashboard/HourlyHeatmap";
import ChatPanel from "@/components/chat/ChatPanel";

export default function DashboardPage() {
  return (
    <div className="flex h-[calc(100vh-48px)]">
      {/* Left column — scrollable */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <KPIStrip />
        <AlertFeed />
        <ScamBreakdown />
        <HourlyHeatmap />
      </div>

      {/* Right column — chat panel fixed 320px */}
      <div className="w-80 border-l border-border/50 bg-white/30 backdrop-blur-[2px] p-3 flex flex-col min-h-0">
        <ChatPanel />
      </div>
    </div>
  );
}
