"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import type { ReactNode } from "react";
import { useAuth } from "@/hooks/useAuth";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/jobs", label: "Jobs" },
  { href: "/jobs/new", label: "Add Job" },
  { href: "/applications", label: "Applications" },
  { href: "/profile", label: "Profile" },
];

export function AuthShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isLoading, logout, user } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated && (pathname === "/login" || pathname === "/register")) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  const publicShell = !isAuthenticated;

  if (publicShell) {
    return (
      <div className="min-h-screen">
        <header className="border-b border-slate-200 bg-white">
          <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              ApplyPilot
            </Link>
            <div className="flex items-center gap-3 text-sm">
              <Link className="font-medium text-slate-700 hover:text-slate-950" href="/login">
                Login
              </Link>
              <Link className="rounded-md bg-slate-950 px-3 py-2 font-medium text-white" href="/register">
                Register
              </Link>
            </div>
          </nav>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">{children}</main>
      </div>
    );
  }

  function isActive(href: string): boolean {
    if (href === "/jobs") {
      return pathname === "/jobs" || (pathname.startsWith("/jobs/") && pathname !== "/jobs/new");
    }
    return pathname === href;
  }

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-slate-50 lg:grid lg:grid-cols-[240px_minmax(0,1fr)]">
      <aside className="hidden border-r border-slate-200 bg-white lg:flex lg:min-h-screen lg:flex-col">
        <div className="border-b border-slate-200 px-5 py-5">
          <Link href="/dashboard" className="text-lg font-semibold tracking-tight">
            ApplyPilot
          </Link>
          <p className="mt-1 text-xs text-slate-500">New-grad job-fit engine</p>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-md px-3 py-2 text-sm font-medium ${
                isActive(item.href)
                  ? "bg-slate-950 text-white"
                  : "text-slate-700 hover:bg-slate-100 hover:text-slate-950"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="border-t border-slate-200 p-4">
          <p className="truncate text-sm font-medium text-slate-950">{user?.full_name || user?.email}</p>
          <p className="truncate text-xs text-slate-500">{user?.email}</p>
          <button
            className="mt-3 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            type="button"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </aside>

      <div className="min-w-0">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur lg:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <Link href="/dashboard" className="text-lg font-semibold tracking-tight">
              ApplyPilot
            </Link>
            <button className="text-sm font-medium text-slate-700" type="button" onClick={handleLogout}>
              Logout
            </button>
          </div>
          <nav className="flex gap-2 overflow-x-auto px-4 pb-3 text-sm">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`shrink-0 rounded-md px-3 py-2 font-medium ${
                  isActive(item.href) ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">{children}</main>
      </div>
    </div>
  );
}
