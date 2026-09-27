"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function TransformRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/new-transformation/upload");
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="text-center space-y-2">
        <div className="w-8 h-8 border-4 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm font-semibold text-slate-600">Opening Transform Workspace...</p>
      </div>
    </div>
  );
}
