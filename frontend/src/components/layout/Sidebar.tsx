"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderOpen,
  FileText,
  Settings,
  Scale,
  ChevronRight,
  Plus,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/matters", label: "Matters Directory", icon: FolderOpen },
  { href: "/documents", label: "Templates & SOPs", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 min-h-screen bg-[#0c0818] border-r border-purple-900/20 flex flex-col shrink-0 relative z-20">
      {/* Brand Header */}
      <div className="p-6 border-b border-purple-900/20 bg-purple-950/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-purple-800/80 border border-purple-600/40 rounded-xl flex items-center justify-center shadow-sm">
            <Scale className="w-4 h-4 text-purple-200" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="text-sm font-bold text-white tracking-wide">
                LegalDoc AI
              </h1>
              <Sparkles className="w-3 h-3 text-purple-400" />
            </div>
            <p className="text-[11px] text-purple-300/50 font-medium">Enterprise Legal Suite</p>
          </div>
        </div>
      </div>

      {/* Quick Action Button */}
      <div className="px-4 pt-5 pb-2">
        <Link href="/matters/new">
          <button className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-purple-700 hover:bg-purple-600 text-white text-xs font-semibold rounded-xl border border-purple-500/30 transition-all shadow-sm">
            <Plus className="w-4 h-4" />
            <span>Create New Matter</span>
          </button>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));

          return (
            <Link key={item.href} href={item.href}>
              <div
                className={cn(
                  "flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all group relative",
                  isActive
                    ? "bg-purple-950/50 text-purple-200 font-semibold border border-purple-800/40"
                    : "text-purple-300/60 hover:text-white hover:bg-purple-950/20"
                )}
              >
                {isActive && (
                  <div className="absolute left-0 top-2 bottom-2 w-1 bg-purple-500 rounded-r-full" />
                )}
                <Icon
                  className={cn(
                    "w-4 h-4 shrink-0",
                    isActive ? "text-purple-400" : "text-purple-300/40 group-hover:text-purple-300"
                  )}
                />
                <span className="flex-1">{item.label}</span>
                {isActive && (
                  <ChevronRight className="w-3.5 h-3.5 text-purple-400" />
                )}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Production Footer */}
      <div className="p-4 border-t border-purple-900/20 bg-purple-950/10">
        <div className="flex items-center justify-between text-xs text-purple-300/40">
          <span className="font-mono text-[10px]">v1.0.0 Enterprise</span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-[10px]">Engine Ready</span>
          </span>
        </div>
      </div>
    </aside>
  );
}
