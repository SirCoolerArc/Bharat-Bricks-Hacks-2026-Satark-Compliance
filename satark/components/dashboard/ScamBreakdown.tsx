"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { fetchScamTaxonomy } from "@/lib/data";
import { ScamTaxonomyRow } from "@/lib/types";

function getBarColor(index: number): string {
  if (index < 2) return "#DC2626";
  if (index < 4) return "#D97706";
  return "#9CA3AF";
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{ payload: ScamTaxonomyRow }>;
}

function CustomTooltip({ active, payload }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-sidebar text-white text-xs px-3 py-2 rounded border border-white/10 shadow-lg backdrop-blur-md">
      <p className="font-semibold mb-1">{d.scam_type}</p>
      <p>{d.complaint_count.toLocaleString()} complaints</p>
      <p>₹{(d.total_loss / 100000).toFixed(2)}L total loss</p>
    </div>
  );
}

export default function ScamBreakdown() {
  const [data, setData] = useState<ScamTaxonomyRow[] | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const result = await fetchScamTaxonomy();
        // Sort by total_loss descending and take top 6 to avoid clutter
        const sorted = [...result].sort((a, b) => b.total_loss - a.total_loss).slice(0, 6);
        setData(sorted);
      } catch (err) {
        console.error("Failed to load scam taxonomy", err);
      }
    }
    load();
  }, []);

  return (
    <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl overflow-hidden flex flex-col min-h-[320px]">
      <div className="px-5 py-4 border-b border-border/50 bg-white/40 flex items-center justify-between">
        <h2 className="text-body font-semibold text-text-primary">
          Scam Loss Distribution
        </h2>
        <span className="text-[10px] text-text-muted font-medium bg-gray-100 px-2 py-0.5 rounded-full">Top 6 by Volume</span>
      </div>
      <div className="px-5 py-6 flex-1 flex flex-col justify-center">
        {!data && (
          <div className="w-full flex justify-center text-text-muted text-sm animate-pulse">
            Aggregating taxonomy...
          </div>
        )}
        {data && data.length === 0 && (
          <div className="w-full flex justify-center text-text-muted text-sm">
            Insufficient data for breakdown.
          </div>
        )}
        {data && data.length > 0 && (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 0, right: 30, bottom: 0, left: 10 }}
              barSize={20}
            >
              <XAxis
                type="number"
                tick={{ fontSize: 10, fill: "#9CA3AF", fontWeight: 500 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v: number) => `₹${(v / 100000).toFixed(0)}L`}
                hide
              />
              <YAxis
                type="category"
                dataKey="scam_type"
                tick={{ fontSize: 10, fill: "#4B5563", fontWeight: 600 }}
                axisLine={false}
                tickLine={false}
                width={120}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(0,0,0,0.02)" }} />
              <Bar dataKey="total_loss" radius={[0, 4, 4, 0]} animationDuration={1500}>
                {data.map((_, index) => (
                  <Cell 
                    key={index} 
                    fill={index === 0 ? "#B91C1C" : index === 1 ? "#DC2626" : index === 2 ? "#EA580C" : "#9CA3AF"} 
                    fillOpacity={1 - (index * 0.12)}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
