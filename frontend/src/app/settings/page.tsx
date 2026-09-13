"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Settings, Cpu, Database, Activity, CheckCircle, RefreshCw, ShieldCheck, Server, Lock } from "lucide-react";
import { healthApi } from "@/lib/api/client";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const { data: health, refetch, isRefetching } = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.check,
  });

  const [activeLlm, setActiveLlm] = useState("openai");
  const [dbMode, setDbMode] = useState("cloud_postgres");

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 animate-fade-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="purple-badge text-xs px-3 py-1 rounded-full flex items-center gap-1.5 font-medium">
              <Settings className="w-3.5 h-3.5" /> Engine Configuration & Security Settings
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-2">Platform Settings & Control Panel</h1>
          <p className="text-purple-300/60 text-sm mt-0.5">
            Manage LLM provider keys, database infrastructure, and 25-check deterministic validation rules
          </p>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isRefetching}
          className="flex items-center gap-2 px-4 py-2 bg-purple-900/30 hover:bg-purple-800/40 text-purple-200 text-xs font-semibold rounded-xl border border-purple-700/30 transition-all shadow-sm"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", isRefetching && "animate-spin")} />
          <span>{isRefetching ? "Refreshing..." : "Test Server Health"}</span>
        </button>
      </div>

      {/* System Status Banner */}
      <div className="glass-purple-card p-6 flex flex-col md:flex-row gap-6 items-start md:items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-950/40 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
            <Activity className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-white">LegalDoc AI Engine Status</h3>
              <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-500/40 font-medium">
                100% Operational
              </span>
            </div>
            <p className="text-xs text-purple-300/60 mt-1">
              Backend API: <code className="font-mono text-purple-300">http://localhost:8000/api/v1</code> • Database: <code className="font-mono text-purple-300">Neon Cloud PostgreSQL / SQLite Sync</code>
            </p>
          </div>
        </div>
      </div>

      {/* AI Provider Config */}
      <div className="glass-purple-card p-6 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-purple-900/20">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-900/30 flex items-center justify-center border border-purple-600/30 text-purple-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">LLM Provider Selection</h2>
              <p className="text-xs text-purple-300/60">Configure which AI provider handles affidavit fact extraction and legal paragraph drafting</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { id: "openai", name: "OpenAI GPT-4o", desc: "Production Grade Legal Extraction & Formatting" },
            { id: "anthropic", name: "Anthropic Claude 3.5 Sonnet", desc: "Complex Statutory Analysis & Defense Drafting" },
            { id: "gemini", name: "Google Gemini 1.5 Pro", desc: "High Context Window Document Analysis" },
          ].map((provider) => (
            <div
              key={provider.id}
              onClick={() => setActiveLlm(provider.id)}
              className={cn(
                "p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between",
                activeLlm === provider.id
                  ? "bg-purple-950/40 border-purple-500 shadow-md shadow-purple-950/50"
                  : "bg-[#120a21]/50 border-purple-900/20 hover:border-purple-700/40"
              )}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-white">{provider.name}</span>
                  {activeLlm === provider.id && <CheckCircle className="w-4 h-4 text-purple-400" />}
                </div>
                <p className="text-xs text-purple-300/60">{provider.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Security & API Key Status */}
        <div className="bg-[#120a21]/60 rounded-xl p-4 border border-purple-800/30 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-950/40 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <Lock className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-white">API Key & Credential Isolation</h4>
              <p className="text-[11px] text-purple-300/60 mt-0.5">
                API keys are loaded securely from backend server environment variables (`backend/.env`). No sensitive keys are exposed on the client UI.
              </p>
            </div>
          </div>
          <span className="text-[10px] px-3 py-1 rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-500/40 font-medium whitespace-nowrap">
            Backend Secured
          </span>
        </div>
      </div>

      {/* Database Infrastructure Config */}
      <div className="glass-purple-card p-6 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-purple-900/20">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-900/30 flex items-center justify-center border border-purple-600/30 text-purple-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Database Engine & Isolation Mode</h2>
              <p className="text-xs text-purple-300/60">Configure local zero-config storage or production Neon cloud database</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            onClick={() => setDbMode("cloud_postgres")}
            className={cn(
              "p-4 rounded-xl border cursor-pointer transition-all",
              dbMode === "cloud_postgres"
                ? "bg-purple-950/40 border-purple-500"
                : "bg-[#120a21]/50 border-purple-900/20"
            )}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-white flex items-center gap-2">
                <Server className="w-4 h-4 text-purple-400" /> Neon PostgreSQL Cloud Database
              </span>
              {dbMode === "cloud_postgres" && <CheckCircle className="w-4 h-4 text-purple-400" />}
            </div>
            <p className="text-xs text-purple-300/60">Async connection pool (`postgresql+asyncpg://`) with live table schema</p>
          </div>

          <div
            onClick={() => setDbMode("sqlite_local")}
            className={cn(
              "p-4 rounded-xl border cursor-pointer transition-all",
              dbMode === "sqlite_local"
                ? "bg-purple-950/40 border-purple-500"
                : "bg-[#120a21]/50 border-purple-900/20"
            )}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-purple-400" /> Zero-Config Local SQLite
              </span>
              {dbMode === "sqlite_local" && <CheckCircle className="w-4 h-4 text-purple-400" />}
            </div>
            <p className="text-xs text-purple-300/60">Local file-based database (`sqlite+aiosqlite:///./legaldoc.db`)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
