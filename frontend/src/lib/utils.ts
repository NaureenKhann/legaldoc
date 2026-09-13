import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "Recently Created";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return "Recently Created";
    return d.toLocaleDateString("en-IN", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "Recently Created";
  }
}

export function formatScore(score: number): string {
  if (score === undefined || score === null || isNaN(score)) return "0/100";
  return `${score.toFixed(1)}/100`;
}

export function getGradeColor(grade: string): string {
  switch (grade) {
    case "A": return "text-emerald-400";
    case "B": return "text-blue-400";
    case "C": return "text-amber-400";
    case "D": return "text-orange-400";
    case "F": return "text-rose-400";
    default: return "text-purple-300/60";
  }
}

export function getStatusColor(status: string | null | undefined): string {
  if (!status) return "bg-purple-950/40 text-purple-300 border-purple-800/40";
  switch (status.toUpperCase()) {
    case "COMPLETED": return "bg-emerald-950/50 text-emerald-400 border-emerald-500/40";
    case "RUNNING": case "GENERATING": case "VALIDATING": case "EXTRACTING":
      return "bg-blue-950/50 text-blue-400 border-blue-500/40";
    case "FAILED": return "bg-rose-950/50 text-rose-400 border-rose-500/40";
    case "NEEDS_REVIEW": return "bg-amber-950/50 text-amber-400 border-amber-500/40";
    default: return "bg-purple-950/40 text-purple-300/80 border-purple-800/40";
  }
}

export function truncate(str: string | null | undefined, max = 100): string {
  if (!str) return "";
  return str.length > max ? str.slice(0, max) + "..." : str;
}
