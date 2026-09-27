"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { historyApi, HistoryItem, OutputType } from "@/lib/api";
import { OUTPUT_TYPE_REGISTRY, ALL_OUTPUT_TYPES } from "@/components/output-cards";
import { Badge } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";
import { Skeleton } from "@/components/shared/Skeleton";
import {
  History,
  Search,
  Filter,
  Calendar,
  ArrowRight,
  FileText,
  Sparkles,
} from "lucide-react";

export default function HistoryPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [outputFilter, setOutputFilter] = useState<string>("all");
  const [sortOrder, setSortOrder] = useState<"newest" | "oldest">("newest");

  const { data: historyItems, isLoading, error } = useQuery<HistoryItem[]>({
    queryKey: ["transformation-history"],
    queryFn: () => historyApi.list(50),
  });

  const filteredItems = (historyItems || [])
    .filter((item) => {
      // Search filter
      const matchesSearch =
        !searchQuery.trim() ||
        item.document_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.job_id.toLowerCase().includes(searchQuery.toLowerCase());

      // Output type filter
      const matchesOutput =
        outputFilter === "all" ||
        item.selected_outputs.includes(outputFilter as OutputType);

      return matchesSearch && matchesOutput;
    })
    .sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return sortOrder === "newest" ? dateB - dateA : dateA - dateB;
    });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge variant="success">Completed</Badge>;
      case "completed_with_warnings":
        return <Badge variant="warning">Warnings</Badge>;
      case "processing":
        return <Badge variant="brand">Processing</Badge>;
      case "failed":
        return <Badge variant="danger">Failed</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-brand-600 mb-1">
            <History className="w-3.5 h-3.5" />
            <span>TRANSFORMATION ARCHIVE</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Transformation History
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Browse and inspect past documents, registered facts, and synthesized output packages.
          </p>
        </div>

        <Link href="/new-transformation/upload">
          <Button size="sm" leftIcon={<Sparkles className="w-4 h-4" />}>
            New Transformation
          </Button>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-4 flex flex-col sm:flex-row items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by document title or Job ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Output Type Filter */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <select
            value={outputFilter}
            onChange={(e) => setOutputFilter(e.target.value)}
            className="p-1.5 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
          >
            <option value="all">All Formats</option>
            {ALL_OUTPUT_TYPES.map((type) => (
              <option key={type} value={type}>
                {OUTPUT_TYPE_REGISTRY[type]?.shortLabel || type}
              </option>
            ))}
          </select>

          {/* Sort */}
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as any)}
            className="p-1.5 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
          </select>
        </div>
      </div>

      {/* History List Table / Cards */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-center justify-between py-3 border-b">
                <div className="space-y-1">
                  <Skeleton className="h-4 w-56" />
                  <Skeleton className="h-3 w-36" />
                </div>
                <Skeleton className="h-6 w-24" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="p-10 text-center text-sm text-red-600">
            Failed to load history items. Backend service may be unreachable.
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <FileText className="w-10 h-10 text-slate-300 mx-auto" />
            <h3 className="text-sm font-bold text-slate-800">
              No matching transformations found
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {searchQuery || outputFilter !== "all"
                ? "Try clearing your filters or search terms."
                : "No past transformations in your workspace archive yet."}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {filteredItems.map((item) => (
              <Link
                key={item.id}
                href={`/results/${item.job_id}`}
                className="flex flex-col sm:flex-row sm:items-center justify-between p-5 hover:bg-slate-50 transition-colors group gap-4"
              >
                <div className="flex items-start gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center shrink-0 mt-0.5 group-hover:bg-brand-600 group-hover:text-white transition-colors">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 group-hover:text-brand-600 transition-colors">
                      {item.document_title || "Untitled Transformation"}
                    </h3>
                    <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
                      <span>Job #{item.job_id.slice(0, 8)}</span>
                      <span>•</span>
                      <span>{new Date(item.created_at).toLocaleString()}</span>
                    </div>

                    {/* Output badges */}
                    <div className="flex flex-wrap gap-1 mt-2.5">
                      {item.selected_outputs.map((type) => (
                        <span
                          key={type}
                          className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200"
                        >
                          {OUTPUT_TYPE_REGISTRY[type]?.shortLabel || type}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between sm:justify-end gap-4">
                  {getStatusBadge(item.status)}
                  <span className="text-xs font-semibold text-brand-600 group-hover:text-brand-700 flex items-center gap-1">
                    View Results
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
