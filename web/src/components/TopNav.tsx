"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import LiveDot from "./LiveDot";

const NAV_ITEMS = [
  { href: "/protect", label: "Protect" },
  { href: "/learn", label: "Learn" },
  { href: "/relief", label: "Relief" },
  { href: "/dashboard", label: "Dashboard" },
];

export default function TopNav() {
  const pathname = usePathname();

  return (
    <nav
      className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm"
      style={{ borderBottom: "0.5px solid var(--border-color)" }}
    >
      <div className="max-w-5xl mx-auto px-4 flex items-center justify-between h-14">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 no-underline">
          <span className="text-lg font-bold tracking-tight text-ink">
            SATARK
          </span>
          <LiveDot />
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {NAV_ITEMS.map(({ href, label }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`
                  px-3 py-1.5 rounded-md text-sm font-medium no-underline transition-colors
                  ${active
                    ? "bg-accent-light text-accent"
                    : "text-ink-muted hover:text-ink hover:bg-surface-100"
                  }
                `}
              >
                {label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
