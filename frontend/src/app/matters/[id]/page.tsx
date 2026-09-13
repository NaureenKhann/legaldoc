"use client";

export const dynamic = "force-dynamic";

import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  FileText,
  Cpu,
  Map,
  Zap,
  Shield,
  BarChart3,
  Download,
  CheckCircle,
  Clock,
  ChevronRight,
  Sparkles,
  ArrowRight,
  AlertTriangle,
  Play,
} from "lucide-react";
import {
  mattersApi,
  documentsApi,
  extractionApi,
  generationApi,
  validationApi,
} from "@/lib/api/client";
import { cn, getStatusColor } from "@/lib/utils";

const STEPS = [
  { key: "documents", label: "Documents", icon: FileText },
  { key: "extraction", label: "Extract", icon: Cpu },
  { key: "mapping", label: "Mapping", icon: Map },
  { key: "generation", label: "Generate", icon: Zap },
  { key: "validation", label: "Validate", icon: Shield },
  { key: "evaluation", label: "Score", icon: BarChart3 },
];

function ActionButton({
  label,
  onClick,
  loading,
  disabled,
  variant = "primary",
}: {
  label: string;
  onClick: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: "primary" | "secondary";
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={cn(
        "px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 shadow-sm",
        variant === "primary"
          ? "bg-purple-700 hover:bg-purple-600 text-white border border-purple-500/30"
          : "bg-purple-950/40 hover:bg-purple-900/40 text-purple-200 border border-purple-800/40",
        (disabled || loading) && "opacity-50 cursor-not-allowed bg-purple-950/20 text-purple-400/40 border-purple-900/10 shadow-none"
      )}
    >
      {loading && (
        <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
      )}
      {label}
    </button>
  );
}

export default function MatterWorkspacePage() {
  const { id: matterId } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();

  const { data: matter } = useQuery({
    queryKey: ["matter", matterId],
    queryFn: () => mattersApi.get(matterId),
  });

  const { data: documents = [] } = useQuery({
    queryKey: ["documents", matterId],
    queryFn: () => documentsApi.list(matterId),
  });

  const { data: caseData } = useQuery({
    queryKey: ["case-data", matterId],
    queryFn: () => extractionApi.getCaseData(matterId),
  });

  const { data: runs = [] } = useQuery({
    queryKey: ["runs", matterId],
    queryFn: () => generationApi.listRuns(matterId),
  });

  const extractMutation = useMutation({
    mutationFn: () => extractionApi.extract(matterId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["case-data", matterId] });
      qc.invalidateQueries({ queryKey: ["matter", matterId] });
    },
  });

  const generateMutation = useMutation({
    mutationFn: () => generationApi.generate(matterId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["runs", matterId] });
      qc.invalidateQueries({ queryKey: ["matter", matterId] });
    },
  });

  const validateMutation = useMutation({
    mutationFn: (runId: string) => validationApi.validate(runId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["runs", matterId] });
      qc.invalidateQueries({ queryKey: ["matter", matterId] });
    },
  });

  const runFullPipeline = async () => {
    try {
      await extractMutation.mutateAsync();
      const run = await generateMutation.mutateAsync();
      if (run?.id) {
        await validateMutation.mutateAsync(run.id);
      }
    } catch (err) {
      console.error("Pipeline run error:", err);
    }
  };

  const isPipelineRunning =
    extractMutation.isPending || generateMutation.isPending || validateMutation.isPending;

  const latestRun = runs[0];

  const docTypeStatus = {
    FORMAT_EXPLANATION: documents.some((d: any) => d.document_type === "FORMAT_EXPLANATION"),
    REFERENCE_AFFIDAVIT: documents.some((d: any) => d.document_type === "REFERENCE_AFFIDAVIT"),
    CASE_INFORMATION: documents.some((d: any) => d.document_type === "CASE_INFORMATION"),
  };

  const hasDocsToExtract = documents.length > 0 || docTypeStatus.CASE_INFORMATION;

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto animate-fade-up">
      {/* Breadcrumb Header */}
      <div>
        <div className="flex items-center gap-2 text-xs text-purple-300/60 mb-2">
          <Link href="/matters" className="hover:text-purple-200 transition-colors">Matters</Link>
          <ChevronRight className="w-3 h-3" />
          <span className="text-purple-200 font-medium">{matter?.title || matterId}</span>
        </div>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white tracking-wide">{matter?.title || "Matter Workspace"}</h1>
          <div className="flex items-center gap-3">
            <button
              onClick={runFullPipeline}
              disabled={isPipelineRunning || !hasDocsToExtract}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-700 to-indigo-600 hover:from-purple-600 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl border border-purple-400/30 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPipelineRunning ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Processing Pipeline...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-white" />
                  <span>Run Full AI Pipeline</span>
                </>
              )}
            </button>
            {matter?.status && (
              <span className={cn("text-xs px-3 py-1 rounded-full border font-medium", getStatusColor(matter.status))}>
                {matter.status}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Pipeline Progress */}
      <div className="glass-purple-card p-5">
        <p className="text-xs text-purple-300/60 uppercase tracking-wider font-semibold mb-4">Pipeline Execution Progress</p>
        <div className="flex items-center justify-between gap-2 overflow-x-auto pb-1">
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            const isDone =
              (step.key === "documents" && hasDocsToExtract) ||
              (step.key === "extraction" && !!caseData) ||
              (step.key === "generation" && latestRun?.status === "COMPLETED") ||
              (step.key === "validation" && !!latestRun?.result);
            return (
              <div key={step.key} className="flex items-center gap-2">
                <div
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium transition-all whitespace-nowrap",
                    isDone
                      ? "bg-emerald-950/40 text-emerald-300 border border-emerald-500/40"
                      : "bg-[#120a21]/60 text-purple-300/40 border border-purple-900/20"
                  )}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{step.label}</span>
                  {isDone && <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />}
                </div>
                {i < STEPS.length - 1 && (
                  <div className={cn("w-6 h-px shrink-0", isDone ? "bg-emerald-500/50" : "bg-purple-900/30")} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column — Documents */}
        <div className="col-span-1 space-y-4">
          <div className="glass-purple-card p-5 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-purple-400" />
              Source Documents ({documents.length})
            </h2>
            {[
              { type: "FORMAT_EXPLANATION", label: "Format Explanation SOP" },
              { type: "REFERENCE_AFFIDAVIT", label: "Reference Reply Model" },
              { type: "CASE_INFORMATION", label: "Case Information Brief" },
            ].map((doc) => {
              const uploaded = docTypeStatus[doc.type as keyof typeof docTypeStatus];
              return (
                <div
                  key={doc.type}
                  className="flex items-center justify-between py-2.5 border-b border-purple-900/20 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    {uploaded ? (
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <Clock className="w-4 h-4 text-purple-400/40" />
                    )}
                    <div>
                      <p className="text-xs font-semibold text-white">{doc.label}</p>
                      <p className={cn("text-[11px]", uploaded ? "text-emerald-400" : "text-purple-300/40")}>
                        {uploaded ? "Ready for Extraction" : "Default SOP Active"}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column — Actions */}
        <div className="col-span-2 space-y-4">
          {/* Extraction */}
          <div className="glass-purple-card p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-purple-400" />
                  Entity Extraction Engine
                </h2>
                <p className="text-xs text-purple-300/60 mt-0.5">Extracts petitioner, respondent & reply facts</p>
              </div>
              <div className="flex gap-2">
                <ActionButton
                  label={extractMutation.isPending ? "Extracting Facts..." : "Run Extraction"}
                  onClick={() => extractMutation.mutate()}
                  loading={extractMutation.isPending}
                  disabled={!hasDocsToExtract}
                />
              </div>
            </div>

            {extractMutation.error && (
              <div className="bg-red-950/40 border border-red-800/50 rounded-xl p-3 text-xs text-red-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                <span>Extraction Error: {(extractMutation.error as any).message || "Failed to extract case facts"}</span>
              </div>
            )}

            {caseData ? (
              <div className="bg-[#120a21]/60 rounded-xl p-4 border border-purple-800/30 text-xs text-purple-300/80 space-y-1">
                <p className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="font-semibold text-white">Extraction Complete</span> • Confidence Score: <span className="text-emerald-400 font-bold">{(caseData.extraction_confidence * 100).toFixed(0)}%</span>
                </p>
                {caseData.unresolved_fields?.length > 0 && (
                  <p className="text-amber-400">⚠️ {caseData.unresolved_fields.length} unresolved fields flagged</p>
                )}
              </div>
            ) : (
              <div className="bg-[#120a21]/40 rounded-xl p-3 border border-purple-900/20 text-xs text-purple-300/60">
                Click <strong>Run Extraction</strong> to extract case facts from uploaded files.
              </div>
            )}
          </div>

          {/* Generation */}
          <div className="glass-purple-card p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Zap className="w-4 h-4 text-purple-400" />
                  Document Assembly & Drafting
                </h2>
                <p className="text-xs text-purple-300/60 mt-0.5">Assembles formal High Court reply draft</p>
              </div>
              <div className="flex gap-2">
                <ActionButton
                  label={generateMutation.isPending ? "Assembling..." : "Generate Affidavit"}
                  onClick={() => generateMutation.mutate()}
                  loading={generateMutation.isPending}
                  disabled={!caseData}
                />
                {latestRun?.status === "COMPLETED" && (
                  <a href={generationApi.downloadUrl(latestRun.id)} download>
                    <ActionButton
                      label="Download DOCX"
                      onClick={() => {}}
                      variant="secondary"
                    />
                  </a>
                )}
              </div>
            </div>

            {generateMutation.error && (
              <div className="bg-red-950/40 border border-red-800/50 rounded-xl p-3 text-xs text-red-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                <span>Generation Error: {(generateMutation.error as any).message || "Failed to assemble affidavit"}</span>
              </div>
            )}

            {latestRun ? (
              <div className="bg-[#120a21]/60 rounded-xl p-4 border border-purple-800/30 text-xs text-purple-300/80 space-y-1">
                <p>Run ID: <span className="text-white font-mono">{latestRun.id?.slice(0, 8)}...</span> • Status: <span className={cn("font-semibold", getStatusColor(latestRun.status))}>{latestRun.status}</span></p>
              </div>
            ) : (
              <div className="bg-[#120a21]/40 rounded-xl p-3 border border-purple-900/20 text-xs text-purple-300/60">
                Run entity extraction first to enable affidavit generation.
              </div>
            )}
          </div>

          {/* Validation */}
          {latestRun?.status === "COMPLETED" && (
            <div className="glass-purple-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Shield className="w-4 h-4 text-purple-400" />
                    25-Check Validation & Quality Scoring
                  </h2>
                  <p className="text-xs text-purple-300/60 mt-0.5">Independent deterministic auditor</p>
                </div>
                <div className="flex gap-2">
                  <ActionButton
                    label={validateMutation.isPending ? "Auditing..." : "Run 25-Check Audit"}
                    onClick={() => validateMutation.mutate(latestRun.id)}
                    loading={validateMutation.isPending}
                  />
                  <Link href={`/matters/${matterId}/evaluation`}>
                    <ActionButton label="View Audit Report →" onClick={() => {}} variant="secondary" />
                  </Link>
                </div>
              </div>

              {validateMutation.error && (
                <div className="bg-red-950/40 border border-red-800/50 rounded-xl p-3 text-xs text-red-300 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                  <span>Audit Error: {(validateMutation.error as any).message || "Failed to execute quality audit"}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
