"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getStoredUser, clearAuthSession, isAuthenticated } from "@/lib/auth";
import { User, API_BASE_URL } from "@/lib/api";
import { Button } from "@/components/shared/Button";
import { Badge } from "@/components/shared/Badge";
import {
  Settings,
  User as UserIcon,
  Building,
  ShieldCheck,
  Server,
  LogOut,
  Mail,
  KeyRound,
  Lock,
  Cpu,
  Globe,
} from "lucide-react";

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    setUser(getStoredUser());
  }, [router]);

  const handleLogout = () => {
    clearAuthSession();
    router.push("/login");
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="pb-4 border-b border-slate-200">
        <div className="flex items-center gap-2 text-xs font-semibold text-brand-600 mb-1">
          <Settings className="w-3.5 h-3.5" />
          <span>CONTENTX ENTERPRISE CONFIGURATION</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          System & Domain Settings
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Manage your enterprise profile, active domain intelligence packs, security limits, and tenancy parameters.
        </p>
      </div>

      {/* Domain Intelligence Packs Configuration Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
        <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-brand-600" /> Active Domain Packs
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-4 rounded-xl border border-red-200 bg-red-50/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-red-900 flex items-center gap-1.5">
                <Lock className="w-4 h-4 text-red-600" /> Cybersecurity Pack
              </span>
              <Badge variant="brand">First-Class</Badge>
            </div>
            <p className="text-[11px] text-red-800 leading-relaxed">
              Strict validation of CVE, CWE, CVSS, IOCs, IP addresses, domains, and cryptographic hashes.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-purple-200 bg-purple-50/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-purple-900 flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-purple-600" /> Blockchain Pack
              </span>
              <Badge variant="brand">First-Class</Badge>
            </div>
            <p className="text-[11px] text-purple-800 leading-relaxed">
              Hex string preservation of 0x contract addresses, transaction hashes, chain IDs, and gas nonces.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-blue-900 flex items-center gap-1.5">
                <Globe className="w-4 h-4 text-blue-600" /> General Domain
              </span>
              <Badge variant="neutral">Base</Badge>
            </div>
            <p className="text-[11px] text-blue-800 leading-relaxed">
              General research, policy, whitepapers, and corporate advisory document transformation.
            </p>
          </div>
        </div>
      </div>

      {/* Profile & Tenancy Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center font-bold text-lg">
              {user?.email ? user.email.charAt(0).toUpperCase() : "U"}
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">
                {user?.email || "Enterprise Architect"}
              </h2>
              <p className="text-xs text-slate-400">
                User ID: {user?.id || "local-session"}
              </p>
            </div>
          </div>
          <Badge variant="brand" size="md">
            Role: {user?.role?.toUpperCase() || "ADMIN"}
          </Badge>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <Mail className="w-3.5 h-3.5 text-brand-600" />
              Email Address
            </div>
            <p className="text-sm font-bold text-slate-900">{user?.email || "—"}</p>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <Building className="w-3.5 h-3.5 text-brand-600" />
              Organization Tenancy
            </div>
            <p className="text-sm font-bold text-slate-900">
              Org #{user?.org_id?.slice(0, 8) || "contentx-enterprise"}
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <Server className="w-3.5 h-3.5 text-emerald-600" />
              Backend Target API
            </div>
            <p className="text-sm font-mono text-slate-800 truncate" title={API_BASE_URL}>
              {API_BASE_URL}
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <KeyRound className="w-3.5 h-3.5 text-brand-600" />
              Session Token Status
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-sm font-bold text-slate-900">Active Bearer JWT</span>
            </div>
          </div>
        </div>
      </div>

      {/* Security & Sign Out Section */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900">End Operator Session</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Signing out will invalidate your local JWT token and redirect you to the login screen.
          </p>
        </div>

        <Button
          variant="danger"
          size="md"
          onClick={handleLogout}
          leftIcon={<LogOut className="w-4 h-4" />}
          data-testid="logout-btn"
        >
          Sign Out
        </Button>
      </div>
    </div>
  );
}

