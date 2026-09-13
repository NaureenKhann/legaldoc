"use client";

import { AlertTriangle } from "lucide-react";

export function DemoModeBanner() {
  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

  if (!isDemoMode) return null;

  return (
    <div className="w-full bg-amber-900/80 border-b border-amber-700 px-4 py-2 flex items-center gap-2 text-amber-200 text-xs font-medium z-50">
      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
      <span>
        <strong>DEMO MODE</strong> — Running with cached extractions. No LLM API
        key required. Generated documents are for demonstration only.
      </span>
    </div>
  );
}
