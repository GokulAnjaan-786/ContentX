"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { setAuthSession } from "@/lib/auth";
import { Button } from "@/components/shared/Button";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Sparkles, Lock, Mail, Building, ShieldCheck } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [orgName, setOrgName] = useState("");
  const [role, setRole] = useState<"operator" | "reviewer" | "org_admin">("operator");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Form field validation
    if (!email.trim() || !password.trim()) {
      setError("Email and password are required.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setIsLoading(true);
    try {
      if (mode === "login") {
        const response = await authApi.login({
          email: email.trim(),
          password,
        });
        setAuthSession(response.access_token, response.user);
        router.push("/dashboard");
      } else {
        const response = await authApi.register({
          email: email.trim(),
          password,
          org_name: orgName.trim() || "Default Org",
          role,
        });
        setAuthSession(response.access_token, response.user);
        router.push("/dashboard");
      }
    } catch (err: any) {
      const msg =
        err?.detail ||
        err?.message ||
        err?.response?.data?.detail ||
        "Authentication failed. Please verify your credentials and try again.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[75vh] flex flex-col items-center justify-center px-4 py-8">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 shadow-md p-8">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-brand-600 text-white flex items-center justify-center mx-auto mb-3 shadow-md shadow-brand-500/20">
            <Sparkles className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            ContentForge <span className="text-brand-600">AI</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Ground-Truth Content Transformation Platform
          </p>
        </div>

        {/* Mode Switcher */}
        <div className="flex rounded-xl bg-slate-100 p-1 mb-6">
          <button
            type="button"
            onClick={() => {
              setMode("login");
              setError(null);
            }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
              mode === "login"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
              mode === "register"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4">
            <ErrorMessage
              title={mode === "login" ? "Sign In Failed" : "Registration Failed"}
              message={error}
            />
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4" data-testid="auth-form">
          <div>
            <label
              htmlFor="email"
              className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1"
            >
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@company.com"
                className="w-full pl-9 pr-3.5 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
                data-testid="email-input"
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1"
            >
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-3.5 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
                data-testid="password-input"
              />
            </div>
          </div>

          {mode === "register" && (
            <>
              <div>
                <label
                  htmlFor="org-name"
                  className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1"
                >
                  Organization Name
                </label>
                <div className="relative">
                  <Building className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    id="org-name"
                    type="text"
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder="Acme Cybersecurity Inc"
                    className="w-full pl-9 pr-3.5 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="role-select"
                  className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1"
                >
                  Workspace Role
                </label>
                <select
                  id="role-select"
                  value={role}
                  onChange={(e) => setRole(e.target.value as any)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="operator">Operator (Create & Transform)</option>
                  <option value="reviewer">Reviewer (Audit & Approve)</option>
                  <option value="org_admin">Organization Admin</option>
                </select>
              </div>
            </>
          )}

          <Button
            type="submit"
            size="lg"
            isLoading={isLoading}
            className="w-full mt-2"
            data-testid="auth-submit-btn"
          >
            {mode === "login" ? "Sign In to ContentForge" : "Create Operator Account"}
          </Button>
        </form>

        {/* Security Assurance Footer */}
        <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>AES-256 JWT Authentication • Tenancy Isolated</span>
        </div>
      </div>
    </div>
  );
}
