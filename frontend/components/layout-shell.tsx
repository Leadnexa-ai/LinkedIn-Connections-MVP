"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PropsWithChildren } from "react";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/create-profile", label: "Create Profile" }
];

export function LayoutShell({ children }: PropsWithChildren) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-canvas">
      <div className="mx-auto flex min-h-screen max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <aside className="hidden w-64 shrink-0 rounded-3xl border border-border bg-panel p-6 shadow-panel md:block">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand">
              LinkedIn Connections
            </p>
            <h1 className="mt-3 text-2xl font-semibold text-ink">Internal Dashboard</h1>
            <p className="mt-2 text-sm text-muted">
              Visualize connection counts and create new profiles without touching the backend yet.
            </p>
          </div>
          <nav className="mt-8 space-y-2">
            {navItems.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`block rounded-2xl px-4 py-3 text-sm font-medium transition ${
                    active
                      ? "bg-brand text-white shadow-sm"
                      : "text-ink hover:bg-slate-100"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
