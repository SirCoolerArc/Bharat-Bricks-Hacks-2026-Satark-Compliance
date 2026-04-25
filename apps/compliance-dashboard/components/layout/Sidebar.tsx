"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  {
    label: "Dashboard",
    href: "/",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="2" y="2" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" fill="currentColor" fillOpacity="0.15" />
        <rect x="11" y="2" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" fill="currentColor" fillOpacity="0.15" />
        <rect x="2" y="11" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" fill="currentColor" fillOpacity="0.15" />
        <rect x="11" y="11" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" fill="currentColor" fillOpacity="0.15" />
      </svg>
    ),
  },
  {
    label: "Geography",
    href: "/geography",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" strokeWidth="1.5" />
        <ellipse cx="10" cy="10" rx="3.5" ry="7.5" stroke="currentColor" strokeWidth="1.5" />
        <line x1="2.5" y1="10" x2="17.5" y2="10" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    ),
  },
  {
    label: "Complaints",
    href: "/complaints",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M10 2a7 7 0 0 1 7 7v3l2 2H1l2-2V9a7 7 0 0 1 7-7z" stroke="currentColor" strokeWidth="1.5" fill="currentColor" fillOpacity="0.1" />
        <path d="M7.5 16a2.5 2.5 0 0 0 5 0" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-14 bg-sidebar/95 backdrop-blur-md shadow-[4px_0_24px_rgba(0,0,0,0.12)] flex flex-col items-center py-4 z-50 border-r border-white/5">
      {/* Logo */}
      <div className="mb-8 flex items-center justify-center w-9 h-9">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M14 2L24 8v12l-10 6L4 20V8l10-6z" stroke="#1D6FA5" strokeWidth="1.5" fill="#1D6FA5" fillOpacity="0.15" />
          <path d="M14 8v8m-4-4h8" stroke="#1D6FA5" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </div>

      {/* Nav items */}
      <nav className="flex flex-col items-center gap-1 flex-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group relative flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-300 ${
                isActive
                  ? "bg-nav-active-bg/90 text-nav-active shadow-sm shadow-nav-active/20"
                  : "text-text-muted hover:text-white hover:bg-white/10"
              }`}
              title={item.label}
            >
              <div className="transform transition-transform duration-300 group-hover:scale-110">
                {item.icon}
              </div>
              {/* Tooltip */}
              <span className="absolute left-14 bg-sidebar/95 backdrop-blur text-white text-xs px-2.5 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-300 whitespace-nowrap z-50 border border-white/10 shadow-lg font-medium">
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
