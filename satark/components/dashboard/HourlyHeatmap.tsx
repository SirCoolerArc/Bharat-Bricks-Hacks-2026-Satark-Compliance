"use client";

import { useEffect, useState } from "react";
import { fetchHourlyPattern } from "@/lib/data";
import { HourlyPatternRow } from "@/lib/types";

function getHeatmapColor(rate: number, maxRate: number): string {
  if (rate === 0) return "bg-gray-100 dark:bg-gray-800/50";
  // Ratio from 0 to 1
  const intensity = Math.min(1, rate / maxRate);
  
  if (intensity < 0.25) return "bg-orange-100 dark:bg-risk-high/10";
  if (intensity < 0.5) return "bg-orange-300 dark:bg-risk-high/30";
  if (intensity < 0.75) return "bg-orange-500 dark:bg-risk-high/60";
  return "bg-risk-high";
}

export default function HourlyHeatmap() {
  const [data, setData] = useState<HourlyPatternRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const result = await fetchHourlyPattern();
        setData(result);
      } catch (err: any) {
        setError(err.message);
      }
    }
    load();
  }, []);

  let peakHour = "-";
  let peakRate = 0;
  let maxRate = 0;
  
  // Prepare an array of 24 hours (0-23) initialized to 0
  const hoursData = Array.from({ length: 24 }).map((_, i) => ({
    hour_of_day: i,
    total_txns: 0,
    fraud_txns: 0,
    fraud_rate_pct: 0
  }));

  if (data && data.length > 0) {
    data.forEach(d => {
      if (d.hour_of_day >= 0 && d.hour_of_day < 24) {
        hoursData[d.hour_of_day] = d;
      }
    });
    
    const peak = [...data].sort((a, b) => b.fraud_rate_pct - a.fraud_rate_pct)[0];
    if (peak) {
      peakHour = `${peak.hour_of_day.toString().padStart(2, "0")}:00`;
      peakRate = peak.fraud_rate_pct;
    }
    
    maxRate = Math.max(...data.map(d => d.fraud_rate_pct), 1);
  }

  return (
    <div className="bg-white/70 shadow-sm border border-border/40 hover:shadow-md transition-all duration-300 rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-border/50 flex flex-wrap items-center justify-between bg-white/40 gap-2">
        <h2 className="text-[13px] font-semibold tracking-wide text-text-primary uppercase flex items-center gap-2">
          <svg className="w-3.5 h-3.5 text-risk-high" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Hourly Risk Heatmap
        </h2>
        {data && (
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-risk-high/10 text-risk-high font-semibold border border-risk-high/20">
            Peak: {peakHour} ({peakRate.toFixed(1)}%)
          </span>
        )}
      </div>
      <div className="px-5 py-6">
        {!data && !error && (
          <div className="flex items-center justify-center h-[120px] text-text-muted text-[11px] border border-dashed border-border/50 rounded-lg">
            <span className="animate-pulse">Loading analytics insights...</span>
          </div>
        )}
        {data && data.length === 0 && !error && (
          <div className="flex items-center justify-center h-[120px] text-text-muted text-[11px] border border-dashed border-border/50 rounded-lg bg-surface-alt/50">
            <span>0 records. Pipeline pending.</span>
          </div>
        )}
        {error && (
          <div className="flex items-center justify-center h-[120px] text-risk-high text-xs">
            Failed to load: {error}
          </div>
        )}
        {data && data.length > 0 && (
          <div className="flex flex-col gap-2 relative">
            
            {/* Hour labels (0, 6, 12, 18, 23) */}
            <div className="flex justify-between text-[10px] text-text-muted font-mono font-medium mb-1 px-1">
              <span>00h</span>
              <span>06h</span>
              <span>12h</span>
              <span>18h</span>
              <span>23h</span>
            </div>

            {/* The Grid */}
            <div className="grid grid-cols-24 gap-1 w-full" style={{ gridTemplateColumns: 'repeat(24, minmax(0, 1fr))' }}>
              {hoursData.map((d, i) => (
                 <div
                   key={i}
                   className="group relative flex flex-col items-center"
                 >
                   <div 
                     className={`w-full aspect-square rounded-[3px] transition-all transform hover:scale-110 hover:ring-2 hover:ring-white shadow-sm hover:z-10 ${getHeatmapColor(d.fraud_rate_pct, maxRate)}`}
                   />
                   
                   {/* Tooltip on hover */}
                   <div className="absolute bottom-full mb-2 hidden group-hover:flex flex-col items-center z-20">
                     <div className="bg-sidebar text-white text-[10px] whitespace-nowrap px-2.5 py-1.5 rounded-md shadow-lg border border-white/10 flex flex-col items-center">
                       <span className="font-semibold text-brand-blue mb-0.5 uppercase tracking-wider">{d.hour_of_day.toString().padStart(2, "0")}:00</span>
                       <span className="text-white/90">{d.total_txns.toLocaleString()} calls</span>
                       <span className="text-risk-high font-medium">{d.fraud_rate_pct.toFixed(1)}% risk</span>
                     </div>
                     <div className="w-0 h-0 border-l-[4px] border-r-[4px] border-t-[5px] border-l-transparent border-r-transparent border-t-sidebar border-b-0 -mt-px relative z-20"></div>
                   </div>
                 </div>
              ))}
            </div>
            
            <div className="flex justify-end items-center gap-1.5 mt-3">
              <span className="text-[10px] font-medium text-text-muted uppercase tracking-wider">Safe</span>
              <div className="flex gap-0.5">
                <div className="w-3 h-3 rounded-[2px] bg-gray-100"></div>
                <div className="w-3 h-3 rounded-[2px] bg-orange-100"></div>
                <div className="w-3 h-3 rounded-[2px] bg-orange-300"></div>
                <div className="w-3 h-3 rounded-[2px] bg-orange-500"></div>
                <div className="w-3 h-3 rounded-[2px] bg-risk-high"></div>
              </div>
              <span className="text-[10px] font-medium text-text-muted uppercase tracking-wider">Danger</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
