"use client";

export const dynamic = "force-dynamic";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { evaluationApi } from "@/lib/api/client";
import { generationApi } from "@/lib/api/client";
import { cn, getGradeColor } from "@/lib/utils";
import { Download, CheckCircle, XCircle, AlertTriangle, Bot, Shield } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";

function ScoreBadge({ score, grade }: { score: number; grade: string }) {
  const colors = {
    A: "from-green-600 to-emerald-600",
    B: "from-blue-600 to-cyan-600",
    C: "from-yellow-600 to-amber-600",
    D: "from-orange-600 to-red-600",
    F: "from-red-700 to-rose-800",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-3 bg-gradient-to-r px-6 py-4 rounded-2xl",
        colors[grade as keyof typeof colors] || "from-gray-700 to-gray-800"
      )}
    >
      <span className="text-5xl font-black text-white">{score.toFixed(0)}</span>
      <div>
        <p className="text-white/70 text-xs uppercase tracking-wider">Score</p>
        <p className="text-white font-bold text-xl">Grade {grade}</p>
        <p className="text-white/60 text-xs">out of 100</p>
      </div>
    </div>
  );
}

function CategoryBar({ name, earned, max }: { name: string; earned: number; max: number }) {
  const pct = Math.round((earned / max) * 100);
  const barColor =
    pct >= 80 ? "bg-green-500" : pct >= 60 ? "bg-blue-500" : pct >= 40 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1.5">
        <span className="text-gray-300 font-medium">{name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</span>
        <span className="text-gray-400">
          {earned.toFixed(1)}/{max}
        </span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-700", barColor)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function CheckRow({ check }: { check: any }) {
  const statusIcon =
    check.status === "PASS" ? (
      <CheckCircle className="w-4 h-4 text-green-400" />
    ) : check.status === "FAIL" ? (
      <XCircle className="w-4 h-4 text-red-400" />
    ) : (
      <AlertTriangle className="w-4 h-4 text-yellow-400" />
    );

  return (
    <div className={cn(
      "p-3 rounded-lg border text-xs",
      check.status === "PASS"
        ? "bg-green-900/10 border-green-800/50"
        : check.status === "FAIL"
        ? "bg-red-900/10 border-red-800/50"
        : "bg-yellow-900/10 border-yellow-800/50"
    )}>
      <div className="flex items-start gap-2">
        <div className="mt-0.5">{statusIcon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <code className="text-gray-300 font-mono text-xs">{check.check_id}</code>
            <span className="text-gray-600 px-1.5 py-0.5 bg-gray-800 rounded text-xs">{check.category}</span>
            <span className={cn(
              "px-1.5 py-0.5 rounded text-xs font-medium",
              check.severity === "ERROR" ? "text-red-400 bg-red-900/30" : "text-yellow-400 bg-yellow-900/30"
            )}>{check.severity}</span>
          </div>
          <p className="text-gray-400 mt-1">{check.message}</p>
          {check.expected && (
            <p className="text-gray-600 mt-1">Expected: <span className="text-gray-400">{check.expected}</span></p>
          )}
          {check.actual && check.actual !== "Present" && (
            <p className="text-gray-600">Actual: <span className="text-gray-400">{check.actual}</span></p>
          )}
          {check.suggested_correction && (
            <p className="text-blue-400 mt-1">💡 {check.suggested_correction}</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function EvaluationPage() {
  const { id: matterId } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<"overview" | "checks" | "report" | "ai">("overview");

  const { data: runs = [] } = useQuery({
    queryKey: ["runs", matterId],
    queryFn: () => generationApi.listRuns(matterId),
  });

  const latestRun = runs[0];

  const { data: evalData, isLoading } = useQuery({
    queryKey: ["evaluation", latestRun?.id],
    queryFn: () => evaluationApi.getReport(latestRun.id),
    enabled: !!latestRun?.id,
  });

  if (!latestRun) {
    return (
      <div className="p-8 text-center text-gray-500">
        <Shield className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p>No generation run found. Generate a document first.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-8 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 shimmer rounded-xl" />
        ))}
      </div>
    );
  }

  if (!evalData) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>Run validation to see the evaluation report.</p>
      </div>
    );
  }

  const report = evalData.report;
  const score = report.score;
  const failedChecks = report.all_issues?.filter((i: any) => i.status === "FAIL") || [];
  const warningChecks = report.all_issues?.filter((i: any) => i.status === "WARNING") || [];

  return (
    <div className="p-8 space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Evaluation Report</h1>
          <p className="text-gray-400 text-xs mt-1">Generation Run: <code className="text-gray-300">{latestRun.id?.slice(0, 12)}...</code></p>
        </div>
        <div className="flex gap-2">
          <a href={evaluationApi.downloadUrl(latestRun.id, "docx")} download>
            <button className="flex items-center gap-2 px-3 py-2 text-xs bg-purple-900/40 hover:bg-purple-800/50 border border-purple-700/40 text-purple-200 rounded-lg transition-colors font-medium">
              <Download className="w-3.5 h-3.5" />
              DOCX
            </button>
          </a>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-2 px-3 py-2 text-xs bg-purple-900/40 hover:bg-purple-800/50 border border-purple-700/40 text-purple-200 rounded-lg transition-colors font-medium"
          >
            <Download className="w-3.5 h-3.5" />
            PDF / Print
          </button>
          <a href={evaluationApi.downloadUrl(latestRun.id, "markdown")} download>
            <button className="flex items-center gap-2 px-3 py-2 text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 rounded-lg transition-colors">
              <Download className="w-3.5 h-3.5" />
              Markdown
            </button>
          </a>
          <a href={evaluationApi.downloadUrl(latestRun.id, "json")} download>
            <button className="flex items-center gap-2 px-3 py-2 text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 rounded-lg transition-colors">
              <Download className="w-3.5 h-3.5" />
              JSON
            </button>
          </a>
        </div>
      </div>

      {/* Score card */}
      <div className="glass-card p-6">
        <div className="flex items-start gap-8">
          <ScoreBadge score={score.overall_score} grade={score.grade} />
          <div className="flex-1 grid grid-cols-3 gap-4">
            {[
              { label: "Passed", value: report.all_issues ? 25 - failedChecks.length - warningChecks.length : "–", color: "text-green-400" },
              { label: "Failed", value: failedChecks.length, color: "text-red-400" },
              { label: "Warnings", value: warningChecks.length, color: "text-yellow-400" },
            ].map((stat) => (
              <div key={stat.label} className="bg-gray-800/50 rounded-lg p-4 text-center">
                <p className={cn("text-2xl font-bold", stat.color)}>{stat.value}</p>
                <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-4">{score.scoring_explanation}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-800/50 rounded-lg p-1 w-fit">
        {[
          { key: "overview", label: "Category Scores" },
          { key: "checks", label: `Issues (${failedChecks.length + warningChecks.length})` },
          { key: "report", label: "Full Report" },
          { key: "ai", label: "AI Review" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={cn(
              "px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
              activeTab === tab.key
                ? "bg-blue-600 text-white"
                : "text-gray-400 hover:text-white"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="glass-card p-6 space-y-4">
          {score.categories.map((cat: any) => (
            <div key={cat.category}>
              <CategoryBar name={cat.category} earned={cat.earned_points} max={cat.max_points} />
              <p className="text-xs text-gray-600 mt-1">{cat.explanation}</p>
            </div>
          ))}
        </div>
      )}

      {activeTab === "checks" && (
        <div className="space-y-2">
          {failedChecks.length === 0 && warningChecks.length === 0 ? (
            <div className="glass-card p-8 text-center text-gray-500">
              <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-400 opacity-50" />
              <p>No issues detected!</p>
            </div>
          ) : (
            [...failedChecks, ...warningChecks].map((check: any, i: number) => (
              <CheckRow key={i} check={check} />
            ))
          )}
        </div>
      )}

      {activeTab === "report" && (
        <div className="glass-card p-6">
          <div className="prose prose-invert prose-sm max-w-none legal-preview">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.report_markdown}</ReactMarkdown>
          </div>
        </div>
      )}

      {activeTab === "ai" && (
        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Bot className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold text-white">AI Semantic Review</h2>
            <span className="text-xs px-2 py-0.5 bg-purple-900/30 border border-purple-800 rounded text-purple-400">
              AI-Generated — Advisory Only
            </span>
          </div>
          <div className="bg-purple-900/10 border border-purple-800/30 rounded-lg p-4 mb-4">
            <p className="text-xs text-purple-300">
              ⚠️ These findings are generated by an AI review layer and are ADVISORY only.
              They do NOT override the deterministic checks above.
            </p>
          </div>
          {report.ai_review_warnings?.length === 0 ? (
            <p className="text-sm text-gray-500">No AI review warnings detected.</p>
          ) : (
            <ul className="space-y-2">
              {report.ai_review_warnings?.map((w: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                  <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 shrink-0" />
                  {w}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
