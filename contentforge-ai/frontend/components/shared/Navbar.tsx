"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ShieldCheck,
  LayoutDashboard,
  Upload,
  FileText,
  History,
  LogOut,
  User as UserIcon,
} from "lucide-react";
import { getStoredUser, clearAuthSession } from "@/lib/auth";
import { User } from "@/lib/api";

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, [pathname]);

  const handleLogout = () => {
    clearAuthSession();
    router.push("/login");
  };

  if (pathname === "/login") {
    return null;
  }

  const primaryNavItems = [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "New Transformation", href: "/new-transformation/upload", icon: Upload },
    { label: "Output Studio", href: "/output-studio", icon: FileText },
    { label: "History", href: "/history", icon: History },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between gap-4">
          {/* Logo & Tagline */}
          <div className="flex items-center gap-3 shrink-0">
            <Link href="/dashboard" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-700 to-indigo-600 flex items-center justify-center text-white shadow-sm group-hover:from-brand-800 group-hover:to-indigo-700 transition-all">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-xl text-slate-900 tracking-tight">
                    Content<span className="text-brand-600">X</span>
                  </span>
                  <span className="text-[10px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded bg-brand-50 text-brand-700 border border-brand-200">
                    Enterprise
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 font-medium tracking-tight">
                  One Source. Every Format. Verified.
                </span>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="hidden sm:flex items-center gap-1 overflow-x-auto py-1">
            {primaryNavItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/dashboard"
                  ? pathname === "/dashboard"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap ${
                    isActive
                      ? "text-brand-600 bg-brand-50 border border-brand-200"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* User & Actions */}
          <div className="flex items-center gap-3 shrink-0">
            {user ? (
              <div className="flex items-center gap-2">
                <div
                  className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-xs font-medium text-slate-700"
                  title={user.email}
                >
                  <UserIcon className="w-3.5 h-3.5 text-slate-500" />
                  <span className="max-w-[140px] truncate hidden sm:inline">{user.email}</span>
                  <span className="px-1.5 py-0.2 rounded bg-brand-100 text-brand-800 text-[10px] font-bold uppercase">
                    {user.role}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  title="Sign out"
                  className="p-2 rounded-lg text-slate-500 hover:text-red-600 hover:bg-red-50 transition-colors"
                  aria-label="Log out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="text-xs font-bold px-3 py-2 rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
