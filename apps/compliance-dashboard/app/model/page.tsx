"use client";

export default function ModelPerformancePage() {
  return (
    <div className="h-full flex items-center justify-center p-8 min-h-[calc(100vh-48px)]">
      <div className="max-w-2xl w-full text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-nav-active-bg to-blue-50 mb-6 shadow-sm border border-nav-active/10 transition-transform hover:scale-105 duration-300">
          <svg className="w-8 h-8 text-nav-active" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <polyline points="3,17 9,11 13,15 21,7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="9" cy="11" r="2" fill="currentColor" />
            <circle cx="13" cy="15" r="2" fill="currentColor" />
            <circle cx="21" cy="7" r="2" fill="currentColor" />
          </svg>
        </div>
        
        <h1 className="text-3xl font-semibold text-text-primary mb-3">
          Model Performance
        </h1>
        <p className="text-body text-text-secondary max-w-lg mx-auto mb-8 leading-relaxed">
          The machine learning performance metrics and historical training logs for the SATARK core anomaly detection engines are currently being aggregated.
        </p>

        <div className="grid grid-cols-2 gap-6 max-w-lg mx-auto opacity-70">
          <div className="bg-card/80 backdrop-blur-md border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-300 transform hover:-translate-y-1">
            <div className="h-2 w-12 bg-gray-200 rounded-full mb-4" />
            <div className="h-6 w-24 bg-gray-300 rounded mb-2" />
            <div className="h-2 w-full bg-gray-100 rounded" />
          </div>
          <div className="bg-card/80 backdrop-blur-md border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-300 transform hover:-translate-y-1">
            <div className="h-2 w-16 bg-gray-200 rounded-full mb-4" />
            <div className="h-6 w-20 bg-gray-300 rounded mb-2" />
            <div className="h-2 w-full bg-gray-100 rounded" />
          </div>
        </div>

        <div className="mt-10">
          <span className="inline-flex items-center px-4 py-1.5 text-xs font-medium bg-white/60 backdrop-blur-sm text-text-secondary rounded-full border border-border/80 shadow-sm">
            Coming Soon API v1.2
          </span>
        </div>
      </div>
    </div>
  );
}
