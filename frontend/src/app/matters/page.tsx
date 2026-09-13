"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { FolderOpen, Plus, Search, FileText, Trash2, ArrowRight, Sparkles, Filter } from "lucide-react";
import { mattersApi } from "@/lib/api/client";
import { cn, getStatusColor, formatDate } from "@/lib/utils";

export default function MattersListPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const { data: matters = [], isLoading } = useQuery({
    queryKey: ["matters"],
    queryFn: mattersApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => mattersApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["matters"] }),
  });

  const filteredMatters = matters.filter((m: any) => {
    const matchesSearch = (m.title || "").toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || m.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-fade-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Legal Matters Directory</h1>
          <p className="text-purple-300/60 text-sm mt-0.5">
            Manage all active case files, extracted facts, and generated affidavits
          </p>
        </div>

        <Link href="/matters/new">
          <button className="flex items-center gap-2 px-4 py-2.5 bg-purple-700 hover:bg-purple-600 text-white text-sm font-medium rounded-lg transition-all border border-purple-500/30 shadow-sm">
            <Plus className="w-4 h-4" />
            <span>New Matter</span>
          </button>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-purple-card p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-purple-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search matters by title or case reference..."
            className="w-full bg-[#120a21] border border-purple-800/40 rounded-xl pl-10 pr-4 py-2 text-white text-sm placeholder:text-gray-600 focus:outline-none focus:border-purple-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          {["ALL", "CREATED", "COMPLETED", "FAILED"].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={cn(
                "px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all",
                statusFilter === status
                  ? "bg-purple-600 text-white"
                  : "bg-purple-950/30 text-purple-300/60 hover:bg-purple-950/60 hover:text-white"
              )}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Matters Table List */}
      <div className="glass-purple-card overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-purple-950/30 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : filteredMatters.length === 0 ? (
          <div className="text-center py-16 text-purple-300/50">
            <FolderOpen className="w-12 h-12 mx-auto mb-3 opacity-30 text-purple-400" />
            <p className="text-sm font-medium">No legal matters found.</p>
            <Link href="/matters/new">
              <button className="mt-3 text-xs text-purple-400 hover:text-purple-300 font-medium underline">
                Create a new legal matter →
              </button>
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-purple-900/20">
            {filteredMatters.map((matter: any) => (
              <div
                key={matter.id}
                className="p-5 flex items-center justify-between hover:bg-purple-950/20 transition-colors group"
              >
                <div className="flex items-center gap-4 flex-1 min-w-0 pr-4">
                  <div className="w-10 h-10 rounded-xl bg-purple-900/30 flex items-center justify-center border border-purple-700/30 text-purple-400 shrink-0">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <Link href={`/matters/${matter.id}`}>
                      <h3 className="text-sm font-semibold text-white group-hover:text-purple-300 transition-colors truncate">
                        {matter.title}
                      </h3>
                    </Link>
                    <p className="text-xs text-purple-300/50 mt-0.5">
                      Created: {formatDate(matter.created_at)} • Type: {matter.document_type}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span
                    className={cn(
                      "text-xs px-3 py-1 rounded-full border font-medium",
                      getStatusColor(matter.status)
                    )}
                  >
                    {matter.status}
                  </span>

                  <Link href={`/matters/${matter.id}`}>
                    <button className="px-3.5 py-1.5 bg-purple-900/30 hover:bg-purple-800/40 text-purple-200 text-xs font-semibold rounded-lg border border-purple-700/30 transition-all flex items-center gap-1">
                      <span>Open Workspace</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </Link>

                  <button
                    onClick={() => {
                      if (confirm("Are you sure you want to delete this matter?")) {
                        deleteMutation.mutate(matter.id);
                      }
                    }}
                    className="p-2 text-gray-500 hover:text-red-400 transition-colors"
                    title="Delete Matter"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
