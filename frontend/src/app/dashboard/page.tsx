"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  FolderOpen,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Plus,
  Activity,
  AlertTriangle,
  Sparkles,
  Shield,
  Zap,
  ArrowRight,
} from "lucide-react";
import { mattersApi, healthApi } from "@/lib/api/client";
import { cn, getStatusColor, formatDate } from "@/lib/utils";

function StatCard({
  label,
  value,
  icon: Icon,
  color = "purple",
  subtitle,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color?: string;
  subtitle?: string;
}) {
  const colorMap: Record<string, string> = {
    purple: "bg-purple-600/20 text-purple-400 border-purple-500/30",
    green: "bg-emerald-600/20 text-emerald-400 border-emerald-500/30",
    red: "bg-rose-600/20 text-rose-400 border-rose-500/30",
    amber: "bg-amber-600/20 text-amber-400 border-amber-500/30",
  };

  return (
    <div className="glass-purple-card p-5 animate-fade-up">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-purple-300/60 uppercase tracking-wider font-semibold">
            {label}
          </p>
          <p className="text-3xl font-black text-white mt-2">{value}</p>
          {subtitle && (
            <p className="text-xs text-purple-300/40 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={cn("p-3 rounded-xl border shadow-inner", colorMap[color])}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: rawMatters = [], isLoading } = useQuery({
    queryKey: ["matters"],
    queryFn: mattersApi.list,
  });

  const matters = Array.isArray(rawMatters) ? rawMatters : [];

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.check,
    refetchInterval: 30000,
  });

  const completed = matters.filter(
    (m: any) => m?.status === "COMPLETED"
  ).length;
  const failed = matters.filter((m: any) => m?.status === "FAILED").length;
  const inProgress = matters.filter(
    (m: any) => m?.status && !["COMPLETED", "FAILED", "CREATED"].includes(m.status)
  ).length;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto animate-fade-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="purple-badge text-xs px-3 py-1 rounded-full font-medium flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-purple-400 animate-pulse" /> AI Legal Intelligence Platform
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-2">Executive Dashboard</h1>
          <p className="text-purple-300/60 text-sm mt-0.5">
            Real-time matter status, automated entity extraction & 25-check deterministic validation
          </p>
        </div>

        <div className="flex items-center gap-3">
          {health && (
            <div
              className={cn(
                "flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold border backdrop-blur-md",
                health.status === "ok" || health.status === "healthy"
                  ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
                  : "bg-rose-950/40 border-rose-500/40 text-rose-300"
              )}
            >
              <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
              <span>{health.status === "ok" || health.status === "healthy" ? "Engine Active" : "Degraded"}</span>
            </div>
          )}
          <Link href="/matters/new">
            <button className="flex items-center gap-2 px-4 py-2.5 bg-purple-700 hover:bg-purple-600 text-white text-xs font-semibold rounded-xl border border-purple-500/30 transition-all shadow-sm">
              <Plus className="w-4 h-4" />
              <span>New Matter</span>
            </button>
          </Link>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          label="Total Matters"
          value={matters.length}
          icon={FolderOpen}
          color="purple"
          subtitle="All recorded legal files"
        />
        <StatCard
          label="Completed"
          value={completed}
          icon={CheckCircle}
          color="green"
          subtitle="Drafted & score verified"
        />
        <StatCard
          label="In Processing"
          value={inProgress}
          icon={Clock}
          color="amber"
          subtitle="Active pipeline execution"
        />
        <StatCard
          label="Requires Review"
          value={failed}
          icon={XCircle}
          color="red"
          subtitle="Validation flag triggered"
        />
      </div>

      {/* Production AI Pipeline Architecture */}
      <div className="glass-purple-card p-6">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-purple-400" />
          Enterprise AI Workflow Architecture
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { step: "01", label: "Smart Ingestion", desc: "Upload case brief or use High Court approved format SOPs", icon: FileText },
            { step: "02", label: "Entity Extraction", desc: "Regex + LLM parser extracts parties, dates & reply facts", icon: Zap },
            { step: "03", label: "DOCX Generation", desc: "Python-controlled strict layout assembly with zero hallucination", icon: Sparkles },
            { step: "04", label: "25-Check Scoring", desc: "Independent deterministic validation & evaluation report", icon: Shield },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.step} className="bg-[#130b22]/70 rounded-xl p-4 border border-purple-800/30 hover:border-purple-500/40 transition-colors">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold font-mono text-purple-400 bg-purple-950/60 px-2 py-0.5 rounded border border-purple-800/50">
                    {item.step}
                  </span>
                  <Icon className="w-4 h-4 text-purple-400" />
                </div>
                <p className="text-white text-sm font-semibold">{item.label}</p>
                <p className="text-purple-300/60 text-xs mt-1 leading-relaxed">{item.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Matters List */}
      <div className="glass-purple-card p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <FileText className="w-4 h-4 text-purple-400" />
            Recent Legal Matters
          </h2>
          <Link href="/matters" className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1 font-medium">
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 bg-purple-950/30 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : matters.length === 0 ? (
          <div className="text-center py-12 text-purple-300/50">
            <FolderOpen className="w-12 h-12 mx-auto mb-3 opacity-30 text-purple-400" />
            <p className="text-sm">No matters created yet.</p>
            <Link href="/matters/new">
              <button className="mt-3 text-xs text-purple-400 hover:text-purple-300 font-medium underline">
                Create your first matter →
              </button>
            </Link>
          </div>
        ) : (
          <div className="space-y-2.5">
            {matters.slice(0, 6).map((matter: any) => (
              <Link key={matter.id} href={`/matters/${matter.id}`}>
                <div className="flex items-center gap-4 px-4 py-3.5 bg-[#120a21]/50 hover:bg-purple-950/40 border border-purple-900/20 hover:border-purple-700/40 rounded-xl transition-all group">
                  <div className="w-9 h-9 bg-purple-900/30 rounded-xl flex items-center justify-center border border-purple-700/30">
                    <FileText className="w-4 h-4 text-purple-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white font-semibold truncate group-hover:text-purple-300 transition-colors">
                      {matter.title}
                    </p>
                    <p className="text-xs text-purple-300/50 mt-0.5">
                      Created: {formatDate(matter.created_at)}
                    </p>
                  </div>
                  <span
                    className={cn(
                      "text-xs px-3 py-1 rounded-full border font-medium",
                      getStatusColor(matter.status)
                    )}
                  >
                    {matter.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Advisory Note */}
      <div className="flex items-start gap-3 bg-purple-950/30 border border-purple-800/40 rounded-xl p-4">
        <AlertTriangle className="w-4 h-4 text-purple-400 mt-0.5 shrink-0" />
        <p className="text-xs text-purple-300/80 leading-relaxed">
          <strong>Production Compliance Notice:</strong> Draft affidavits generated by LegalDoc AI are governed by 25 deterministic verification checks. Always perform final human advocate review prior to high court submission.
        </p>
      </div>
    </div>
  );
}
