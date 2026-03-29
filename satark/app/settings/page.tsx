"use client";

export default function SettingsPage() {
  return (
    <div className="h-full flex items-center justify-center p-8 min-h-[calc(100vh-48px)]">
      <div className="max-w-2xl w-full text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-risk-med-bg to-orange-50 mb-6 shadow-sm border border-risk-med/10 transition-transform hover:-rotate-12 duration-300">
          <svg className="w-8 h-8 text-risk-med" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        
        <h1 className="text-3xl font-semibold text-text-primary mb-3">
          Compliance Settings
        </h1>
        <p className="text-body text-text-secondary max-w-lg mx-auto mb-8 leading-relaxed">
          The SATARK regulatory framework controls, API configurations, and user permission limits will be accessible here in the next release.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto opacity-70">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-card/80 backdrop-blur-md border border-border rounded-2xl p-5 flex items-center gap-4 text-left shadow-sm hover:shadow-md transition-all duration-300">
              <div className="w-10 h-10 rounded-full bg-gray-100 flex-shrink-0" />
              <div className="flex-1">
                <div className="h-4 w-24 bg-gray-300 rounded mb-2" />
                <div className="h-3 w-full bg-gray-100 rounded" />
              </div>
              <div className="w-8 h-4 bg-gray-200 rounded-full shrink-0" />
            </div>
          ))}
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
