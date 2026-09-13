"use client";

import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Upload, FileText, CheckCircle, AlertCircle, Sparkles, ShieldCheck, ArrowRight } from "lucide-react";
import { mattersApi, documentsApi } from "@/lib/api/client";
import { cn } from "@/lib/utils";

const REQUIRED_DOCS = [
  {
    type: "CASE_INFORMATION",
    label: "Case Information / Brief (Required)",
    description: "Upload petition / case facts document, or launch with High Court sample brief",
    accent: "purple",
    required: true,
  },
  {
    type: "FORMAT_EXPLANATION",
    label: "Court Format Standard (Optional)",
    description: "Leave blank to use pre-configured Bombay High Court Writ Template",
    accent: "indigo",
    required: false,
  },
  {
    type: "REFERENCE_AFFIDAVIT",
    label: "Reference Reply Sample (Optional)",
    description: "Leave blank to use court-approved gold-standard reference reply",
    accent: "violet",
    required: false,
  },
] as const;

type DocType = (typeof REQUIRED_DOCS)[number]["type"];

function FileDropzone({
  doc,
  file,
  onFile,
}: {
  doc: (typeof REQUIRED_DOCS)[number];
  file: File | null;
  onFile: (f: File | null) => void;
}) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    multiple: false,
    noClick: false,
    noKeyboard: false,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/msword": [".doc"],
      "text/plain": [".txt", ".text"],
      "text/markdown": [".md"],
    },
    onDrop: (acceptedFiles) => {
      if (acceptedFiles && acceptedFiles.length > 0) {
        onFile(acceptedFiles[0]);
      }
    },
    onDropRejected: (rejections) => {
      if (rejections && rejections.length > 0 && rejections[0].file) {
        onFile(rejections[0].file);
      }
    },
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "border-2 border-dashed rounded-xl p-5 cursor-pointer transition-all duration-300 relative overflow-hidden group",
        file
          ? "border-emerald-500/50 bg-emerald-950/20 shadow-lg shadow-emerald-950/20"
          : isDragActive
          ? "border-purple-500 bg-purple-950/40 scale-[1.01]"
          : "border-purple-800/40 bg-[#120a21]/60 hover:border-purple-500/60 hover:bg-purple-950/30"
      )}
    >
      <input {...getInputProps()} />
      {file ? (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/20 flex items-center justify-center border border-emerald-500/40 shrink-0">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">{file.name}</p>
              <p className="text-xs text-emerald-400/80 font-medium">
                {(file.size / 1024).toFixed(1)} KB • Selected & Ready
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onFile(null);
            }}
            className="text-xs px-2.5 py-1 rounded-lg bg-purple-900/40 hover:bg-purple-800/60 text-purple-300 border border-purple-700/40 transition-colors"
          >
            Remove
          </button>
        </div>
      ) : (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-purple-900/30 flex items-center justify-center border border-purple-600/40 shrink-0 group-hover:border-purple-400/60 transition-colors">
              <Upload className="w-5 h-5 text-purple-400 group-hover:scale-110 transition-transform" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-semibold text-white">{doc.label}</p>
                {!doc.required && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-900/40 text-purple-300 border border-purple-700/40">
                    Preset Available
                  </span>
                )}
              </div>
              <p className="text-xs text-purple-300/60 mt-0.5">{doc.description}</p>
            </div>
          </div>
          <span className="px-3.5 py-1.5 rounded-lg bg-purple-900/50 group-hover:bg-purple-800/70 text-purple-200 text-xs font-medium border border-purple-700/40 transition-all shrink-0">
            Browse File
          </span>
        </div>
      )}
    </div>
  );
}

export default function NewMatterPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [useDefaultTemplates, setUseDefaultTemplates] = useState(true);
  const [files, setFiles] = useState<Record<DocType, File | null>>({
    FORMAT_EXPLANATION: null,
    REFERENCE_AFFIDAVIT: null,
    CASE_INFORMATION: null,
  });
  const [step, setStep] = useState<"form" | "uploading" | "done">("form");
  const [error, setError] = useState<string | null>(null);

  const createMatter = useMutation({
    mutationFn: (data: { title: string; use_default_templates: boolean }) => mattersApi.create(data),
  });

  // User can submit if title >= 3 AND either they uploaded CASE_INFORMATION OR useDefaultTemplates is enabled
  const canSubmit =
    title.trim().length >= 3 &&
    (files.CASE_INFORMATION !== null || useDefaultTemplates);

  async function handleSubmit() {
    if (!canSubmit) return;
    setStep("uploading");
    setError(null);

    try {
      const matter = await createMatter.mutateAsync({
        title: title.trim(),
        use_default_templates: useDefaultTemplates,
      });

      // Upload Case Information document if user provided one
      if (files.CASE_INFORMATION) {
        const fdCase = new FormData();
        fdCase.append("document_type", "CASE_INFORMATION");
        fdCase.append("file", files.CASE_INFORMATION);
        await documentsApi.upload(matter.id, fdCase);
      }

      // Upload custom format document if provided
      if (files.FORMAT_EXPLANATION) {
        const fdFormat = new FormData();
        fdFormat.append("document_type", "FORMAT_EXPLANATION");
        fdFormat.append("file", files.FORMAT_EXPLANATION);
        await documentsApi.upload(matter.id, fdFormat);
      }

      // Upload custom reference document if provided
      if (files.REFERENCE_AFFIDAVIT) {
        const fdRef = new FormData();
        fdRef.append("document_type", "REFERENCE_AFFIDAVIT");
        fdRef.append("file", files.REFERENCE_AFFIDAVIT);
        await documentsApi.upload(matter.id, fdRef);
      }

      qc.invalidateQueries({ queryKey: ["matters"] });
      setStep("done");
      router.push(`/matters/${matter.id}`);
    } catch (err: any) {
      console.error("Creation error:", err);
      setError(err.message || "File upload failed");
      setStep("form");
    }
  }

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-8 animate-fade-up">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="purple-badge text-xs px-3 py-1 rounded-full flex items-center gap-1.5 font-medium">
            <Sparkles className="w-3.5 h-3.5" /> Production Legal Drafting Engine
          </span>
        </div>
        <h1 className="text-2xl font-bold text-white mt-3">Initiate New Legal Matter</h1>
        <p className="text-purple-300/60 text-sm mt-1">
          Provide the case details below. Our AI Legal Engine will parse the case facts, map them onto court rules, and assemble the draft.
        </p>
      </div>

      <div className="space-y-6">
        {/* Title Card */}
        <div className="glass-purple-card p-6">
          <label className="block text-xs text-purple-300 uppercase tracking-wider font-semibold mb-2">
            Matter Title / Case Reference <span className="text-purple-400">*</span>
          </label>
          <input
            id="matter-title-input"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Writ Petition No. 1847 of 2026 — MMRDA vs Union of India"
            className="w-full bg-[#120a21] border border-purple-800/40 rounded-xl px-4 py-3 text-white text-sm placeholder:text-gray-600 focus:outline-none focus:border-purple-500 transition-colors shadow-inner"
          />
        </div>

        {/* Template Toggle Card */}
        <div className="glass-purple-card p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-purple-900/30 flex items-center justify-center border border-purple-600/30">
                <ShieldCheck className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Use Pre-Configured High Court Template</h3>
                <p className="text-xs text-purple-300/60 mt-0.5">
                  Automatically applies court-approved formatting & reference affidavit rules
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={useDefaultTemplates}
                onChange={(e) => setUseDefaultTemplates(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>
        </div>

        {/* Uploads Card */}
        <div className="glass-purple-card p-6 space-y-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs text-purple-300 uppercase tracking-wider font-semibold">
              Case Documents
            </h3>
            <span className="text-xs text-purple-300/60">
              {useDefaultTemplates ? "Select file (or use default)" : "3 Files Required"}
            </span>
          </div>

          {REQUIRED_DOCS.map((doc) => {
            if (useDefaultTemplates && !doc.required) return null;
            return (
              <FileDropzone
                key={doc.type}
                doc={doc}
                file={files[doc.type]}
                onFile={(f) => setFiles((prev) => ({ ...prev, [doc.type]: f }))}
              />
            );
          })}
        </div>

        {/* Error Notification */}
        {error && (
          <div className="flex items-center gap-3 bg-red-950/40 border border-red-800/60 rounded-xl p-4 text-sm text-red-300 shadow-lg">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {/* Submit Action */}
        <button
          onClick={handleSubmit}
          disabled={!canSubmit || step === "uploading"}
          className={cn(
            "w-full py-4 rounded-xl text-sm font-semibold transition-all duration-300 shadow-xl flex items-center justify-center gap-2",
            canSubmit && step === "form"
              ? "bg-purple-700 hover:bg-purple-600 text-white cursor-pointer border border-purple-500/30"
              : "bg-purple-950/40 text-gray-500 border border-purple-900/20 cursor-not-allowed"
          )}
        >
          {step === "uploading" ? (
            <span className="flex items-center gap-2 text-white">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Ingesting & Extracting Case Facts...
            </span>
          ) : step === "done" ? (
            <span className="flex items-center gap-2 text-emerald-400 font-semibold">
              <CheckCircle className="w-5 h-5" />
              Matter Initialized! Redirecting to Workspace...
            </span>
          ) : (
            <>
              <span>Create Matter & Launch AI Engine</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
