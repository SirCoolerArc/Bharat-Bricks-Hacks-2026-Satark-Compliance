"use client";

import { useState, useMemo, useEffect } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup,
} from "react-simple-maps";
import { fetchGeoHeatmap } from "@/lib/data";
import { GeoHeatmapRow } from "@/lib/types";

const INDIA_TOPO = "/india-states.json";
const MIN_RATE = 6.98;
const MAX_RATE = 8.95;

type SortKey = "fraud_rate_pct" | "fraud_txns" | "total_txns";

// Color interpolation: #DCFCE7 → #991B1B
function getFraudColor(rate: number): string {
  const t = Math.min(1, Math.max(0, (rate - MIN_RATE) / (MAX_RATE - MIN_RATE)));
  let r: number, g: number, b: number;
  if (t < 0.25) {
    const s = t / 0.25;
    r = Math.round(220 + (134 - 220) * s);
    g = Math.round(252 + (239 - 252) * s);
    b = Math.round(231 + (172 - 231) * s);
  } else if (t < 0.5) {
    const s = (t - 0.25) / 0.25;
    r = Math.round(134 + (245 - 134) * s);
    g = Math.round(239 + (158 - 239) * s);
    b = Math.round(172 + (11 - 172) * s);
  } else if (t < 0.75) {
    const s = (t - 0.5) / 0.25;
    r = Math.round(245 + (220 - 245) * s);
    g = Math.round(158 + (38 - 158) * s);
    b = Math.round(11 + (38 - 11) * s);
  } else {
    const s = (t - 0.75) / 0.25;
    r = Math.round(220 + (153 - 220) * s);
    g = Math.round(38 + (27 - 38) * s);
    b = Math.round(38 + (27 - 38) * s);
  }
  return `rgb(${r}, ${g}, ${b})`;
}

export default function GeographyPage() {
  const [data, setData] = useState<GeoHeatmapRow[] | null>(null);
  const [hoveredState, setHoveredState] = useState<GeoHeatmapRow | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [sortBy, setSortBy] = useState<SortKey>("fraud_rate_pct");
  const [position, setPosition] = useState({ coordinates: [81, 23] as [number, number], zoom: 1 });

  useEffect(() => {
    async function init() {
      try {
        const rows = await fetchGeoHeatmap();
        setData(rows);
      } catch (err) {
        console.error("Failed to fetch geo heatmap", err);
      }
    }
    init();
  }, []);

  function handleZoomIn() {
    if (position.zoom >= 4) return;
    setPosition((pos) => ({ ...pos, zoom: pos.zoom * 1.5 }));
  }

  function handleZoomOut() {
    if (position.zoom <= 1) return;
    setPosition((pos) => ({ ...pos, zoom: pos.zoom / 1.5 }));
  }

  function handleMoveEnd(newPosition: { coordinates: [number, number]; zoom: number }) {
    setPosition(newPosition);
  }

  const sortedStates = useMemo(() => {
    if (!data) return [];
    return [...data].sort((a, b) => b[sortBy] - a[sortBy]);
  }, [sortBy, data]);

  const stateMap = useMemo(() => {
    const map = new Map<string, GeoHeatmapRow>();
    if (data) data.forEach((s) => map.set(s.sender_state, s));
    return map;
  }, [data]);

  const highestFraudRate = data && data.length > 0 ? data.reduce((a, b) => (a.fraud_rate_pct > b.fraud_rate_pct ? a : b)) : null;
  const mostFraudTxns = data && data.length > 0 ? data.reduce((a, b) => (a.fraud_txns > b.fraud_txns ? a : b)) : null;
  const mostTotalTxns = data && data.length > 0 ? data.reduce((a, b) => (a.total_txns > b.total_txns ? a : b)) : null;

  return (
    <div className="flex h-[calc(100vh-48px)] p-4 gap-4">
      {/* LEFT: Map (60%) */}
      <div className="w-[60%] overflow-hidden flex flex-col">
        <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-hover transition-all duration-300 rounded-2xl flex-1 flex flex-col overflow-hidden relative group">
          {/* Map header */}
          <div className="px-5 py-4 border-b border-border/50 flex items-center justify-between bg-white/40">
            <h2 className="text-body font-semibold text-text-primary">
              Fraud Rate by State
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-medium text-text-muted">LOW</span>
              {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map((t) => (
                <div
                  key={t}
                  className="w-5 h-2.5 rounded-sm shadow-sm"
                  style={{ backgroundColor: getFraudColor(MIN_RATE + t * (MAX_RATE - MIN_RATE)) }}
                />
              ))}
              <span className="text-[10px] font-medium text-text-muted">HIGH</span>
              <span className="text-[10px] font-mono text-text-muted ml-1 bg-white/50 px-1.5 py-0.5 rounded border border-border/50">
                {MIN_RATE}% – {MAX_RATE}%
              </span>
            </div>
          </div>

          {/* Map Controls */}
          <div className="absolute left-4 top-20 flex flex-col gap-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <button
              onClick={handleZoomIn}
              className="bg-white/90 backdrop-blur border border-border/80 shadow-sm rounded-lg p-2 text-text-secondary hover:text-text-primary hover:bg-white transition-all transform hover:scale-105"
              title="Zoom In"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </button>
            <button
              onClick={handleZoomOut}
              className="bg-white/90 backdrop-blur border border-border/80 shadow-sm rounded-lg p-2 text-text-secondary hover:text-text-primary hover:bg-white transition-all transform hover:scale-105"
              title="Zoom Out"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </button>
            <button
              onClick={() => setPosition({ coordinates: [81, 23], zoom: 1 })}
              className="bg-white/90 backdrop-blur border border-border/80 shadow-sm rounded-lg p-2 text-text-secondary hover:text-text-primary hover:bg-white transition-all transform hover:scale-105 mt-2"
              title="Reset View"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                <polyline points="9 22 9 12 15 12 15 22"></polyline>
              </svg>
            </button>
          </div>

          {/* Map SVG */}
          <div className="flex-1 relative min-h-0 flex items-center justify-center p-0">
            <ComposableMap
              projection="geoMercator"
              projectionConfig={{
                scale: 900,
              }}
              width={600}
              height={550}
              style={{ width: "100%", height: "100%" }}
            >
              <ZoomableGroup
                zoom={position.zoom}
                center={position.coordinates}
                onMoveEnd={handleMoveEnd}
              >
                <Geographies geography={INDIA_TOPO}>
                  {({ geographies }) =>
                    geographies.map((geo) => {
                      const stName = geo.properties.st_nm as string;
                      const info = stateMap.get(stName);
                      const fill = info ? getFraudColor(info.fraud_rate_pct) : "#EAE8E1";

                      return (
                        <Geography
                          key={geo.rsmKey}
                          geography={geo}
                          fill={fill}
                          stroke="#FFFFFF"
                          strokeWidth={0.5 / position.zoom}
                          style={{
                            default: { outline: "none", transition: "all 250ms" },
                            hover: { outline: "none", strokeWidth: 1.5 / position.zoom, stroke: "#1C1C1A", filter: "brightness(0.9) drop-shadow(0px 4px 6px rgba(0,0,0,0.2))" },
                            pressed: { outline: "none" },
                          }}
                          onMouseEnter={() => {
                            if (info) setHoveredState(info);
                          }}
                          onMouseMove={(e) => {
                            setTooltipPos({ x: e.clientX, y: e.clientY });
                          }}
                          onMouseLeave={() => setHoveredState(null)}
                        />
                      );
                    })
                  }
                </Geographies>
              </ZoomableGroup>
            </ComposableMap>

            {/* Tooltip */}
            {hoveredState && (
              <div
                className="fixed z-50 pointer-events-none bg-sidebar/95 backdrop-blur-md text-white text-xs px-4 py-3 rounded-xl border border-white/20 shadow-xl transform -translate-y-1/2"
                style={{
                  left: tooltipPos.x + 12,
                  top: tooltipPos.y - 10,
                }}
              >
                <p className="font-semibold text-[13px] mb-1">{hoveredState.sender_state}</p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                  <span className="text-white/60">Fraud Rate</span>
                  <span className="font-medium text-right">{hoveredState.fraud_rate_pct}%</span>
                  <span className="text-white/60">Fraud Txns</span>
                  <span className="font-medium text-right">{hoveredState.fraud_txns.toLocaleString()}</span>
                  <span className="text-white/60">Total Txns</span>
                  <span className="font-medium text-right">{hoveredState.total_txns.toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* RIGHT: Stats panel (40%) */}
      <div className="w-[40%] overflow-y-auto flex flex-col gap-4">
        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl p-4">
            <p className="text-label uppercase text-text-muted font-medium mb-1">
              Highest Fraud Rate
            </p>
            <p className="text-[16px] font-semibold text-risk-high leading-tight">
              {highestFraudRate?.fraud_rate_pct ?? "0.00"}%
            </p>
            <p className="text-label text-text-muted mt-0.5 truncate">
              {highestFraudRate?.sender_state ?? "Loading..."}
            </p>
          </div>
          <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl p-4">
            <p className="text-label uppercase text-text-muted font-medium mb-1">
              Most Fraud Txns
            </p>
            <p className="text-[16px] font-semibold text-risk-high leading-tight">
              {mostFraudTxns?.fraud_txns.toLocaleString() ?? "0"}
            </p>
            <p className="text-label text-text-muted mt-0.5 truncate">
              {mostFraudTxns?.sender_state ?? "Loading..."}
            </p>
          </div>
          <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl p-4">
            <p className="text-label uppercase text-text-muted font-medium mb-1">
              Most Total Txns
            </p>
            <p className="text-[16px] font-semibold text-risk-med leading-tight">
              {mostTotalTxns?.total_txns.toLocaleString() ?? "0"}
            </p>
            <p className="text-label text-text-muted mt-0.5 truncate">
              {mostTotalTxns?.sender_state ?? "Loading..."}
            </p>
          </div>
        </div>

        {/* Filter buttons */}
        <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card rounded-2xl overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-border/50 flex items-center justify-between bg-white/40">
            <h2 className="text-body font-semibold text-text-primary">
              State Rankings
            </h2>
            <div className="flex gap-1">
              {(
                [
                  { key: "fraud_rate_pct" as SortKey, label: "Fraud Rate" },
                  { key: "fraud_txns" as SortKey, label: "Fraud Txns" },
                  { key: "total_txns" as SortKey, label: "Total Txns" },
                ] as const
              ).map((btn) => (
                <button
                  key={btn.key}
                  onClick={() => setSortBy(btn.key)}
                  className={`text-[10px] px-2 py-1 rounded border transition-colors ${
                    sortBy === btn.key
                      ? "bg-nav-active-bg border-nav-active/30 text-nav-active font-medium"
                      : "border-border text-text-secondary hover:bg-gray-50"
                  }`}
                >
                  {btn.label}
                </button>
              ))}
            </div>
          </div>

          {/* Table header */}
          <div className="grid grid-cols-[24px_1fr_60px_60px_60px] gap-2 px-5 py-2.5 border-b border-border/50 bg-white/30 backdrop-blur">
            <span className="text-label uppercase text-text-muted font-medium">#</span>
            <span className="text-label uppercase text-text-muted font-medium">State</span>
            <span className="text-label uppercase text-text-muted font-medium text-right">Rate</span>
            <span className="text-label uppercase text-text-muted font-medium text-right">Fraud</span>
            <span className="text-label uppercase text-text-muted font-medium text-right">Total</span>
          </div>

          {/* Table rows */}
          <div className="max-h-[calc(100vh-330px)] overflow-y-auto overflow-x-hidden">
            {!data && (
              <div className="flex items-center justify-center p-8 text-sm text-text-muted animate-pulse">
                Loading analytics insights...
              </div>
            )}
            {data && data.length === 0 && (
              <div className="flex items-center justify-center p-8 text-sm text-text-muted bg-white/30 italic">
                0 records found. Awaiting pipeline execution.
              </div>
            )}
            {data && data.length > 0 && sortedStates.map((state, idx) => {
              const isTop3 = idx < 3;
              return (
                <div
                  key={state.sender_state}
                  className={`grid grid-cols-[24px_1fr_60px_60px_60px] gap-2 px-5 py-3 border-b border-border/30 hover:bg-white/60 transition-colors items-center cursor-pointer ${
                    isTop3 ? "bg-risk-high-bg/40" : ""
                  }`}
                  onMouseEnter={() => setHoveredState(state)}
                  onMouseLeave={() => setHoveredState(null)}
                >
                  <span
                    className={`text-label font-mono ${
                      isTop3 ? "text-risk-high font-semibold" : "text-text-muted"
                    }`}
                  >
                    {idx + 1}
                  </span>
                  <span className="text-body text-text-primary truncate">
                    {state.sender_state}
                  </span>
                  <span
                    className={`text-body text-right font-mono font-medium ${
                      state.fraud_rate_pct >= 8.5
                        ? "text-risk-high"
                        : state.fraud_rate_pct >= 8.0
                        ? "text-risk-med"
                        : "text-text-primary"
                    }`}
                  >
                    {state.fraud_rate_pct}%
                  </span>
                  <span className="text-body text-right font-mono text-text-secondary">
                    {state.fraud_txns.toLocaleString()}
                  </span>
                  <span className="text-body text-right font-mono text-text-secondary truncate">
                    {state.total_txns.toLocaleString()}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
