"use client";

import { useState } from "react";
import { FileText, Download, Eye, Sparkles, CheckCircle2, Search, Filter, ShieldCheck, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

const STANDARD_TEMPLATES = [
  {
    id: "sop-01",
    title: "Bombay High Court Writ Petition Affidavit in Reply Format Rules",
    category: "High Court Writs",
    version: "v2026.1 Standard",
    description: "Mandatory 10-section layout specification compliant with High Court Appellate Side Rules.",
    sections: ["Forum Title", "Cause Title", "Deponent Clause", "Preliminary Objections", "Paragraph Reply", "Prayer", "Jurat", "Verification"],
    status: "Active System SOP",
    fileSize: "1.2 MB",
    updatedAt: "September 2026",
  },
  {
    id: "sop-02",
    title: "Gold-Standard Reference Reply Affidavit (Land Acquisition Matter)",
    category: "Land & Urban Development",
    version: "v2026.2 Gold Draft",
    description: "Approved defense model draft for MMRDA/State land acquisition writ petitions.",
    sections: ["MRTP Act Objections", "Possession Receipt Verification", "Public Utility DP Plan Defense"],
    status: "Active System SOP",
    fileSize: "2.4 MB",
    updatedAt: "September 2026",
  },
  {
    id: "sop-03",
    title: "Commercial Division Arbitration & Contract Dispute Reply Model",
    category: "Commercial Division",
    version: "v2026.1 Commercial",
    description: "Pre-structured reply framework for Article 226 contractual dispute objections.",
    sections: ["Disputed Fact Objections", "Demurrage Clause 18.2", "Liquidated Damages Defense"],
    status: "Active System SOP",
    fileSize: "1.8 MB",
    updatedAt: "August 2026",
  },
  {
    id: "sop-04",
    title: "Service & Employment Writ Petition Counter-Affidavit Format",
    category: "Service Matters",
    version: "v2026.1 Service",
    description: "Standard counter-affidavit model for administrative & service tribunal matters.",
    sections: ["Seniority List Verification", "Departmental Enquiry Findings", "Laches & Delay Objections"],
    status: "Available Template",
    fileSize: "1.5 MB",
    updatedAt: "August 2026",
  },
];

export default function DocumentsPage() {
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  const filtered = STANDARD_TEMPLATES.filter((t) => {
    const matchesSearch = t.title.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase());
    const matchesCat = selectedCategory === "All" || t.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="purple-badge text-xs px-3 py-1 rounded-full flex items-center gap-1.5 font-medium">
              <ShieldCheck className="w-3.5 h-3.5" /> High Court Verified Standard Operating Templates
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-2">Templates & Reference SOP Library</h1>
          <p className="text-purple-300/60 text-sm mt-0.5">
            Pre-configured legal structures used by LegalDoc AI for zero-hallucination document assembly
          </p>
        </div>

        <button className="flex items-center gap-2 px-4 py-2.5 btn-purple-gradient text-sm font-semibold rounded-xl transition-all shadow-lg">
          <Plus className="w-4 h-4" />
          <span>Upload Custom Template SOP</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="glass-purple-card p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-purple-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search templates by title, jurisdiction, or clause..."
            className="w-full bg-[#120a21] border border-purple-800/40 rounded-xl pl-10 pr-4 py-2 text-white text-sm placeholder:text-gray-600 focus:outline-none focus:border-purple-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {["All", "High Court Writs", "Land & Urban Development", "Commercial Division", "Service Matters"].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={cn(
                "px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all",
                selectedCategory === cat
                  ? "bg-purple-600 text-white shadow-md shadow-purple-900/40"
                  : "bg-purple-950/30 text-purple-300/60 hover:bg-purple-950/60 hover:text-white"
              )}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filtered.map((doc) => (
          <div key={doc.id} className="glass-purple-card p-6 flex flex-col justify-between group">
            <div>
              <div className="flex items-start justify-between">
                <div className="w-10 h-10 rounded-xl bg-purple-900/30 flex items-center justify-center border border-purple-600/30 text-purple-400 group-hover:scale-110 transition-transform">
                  <FileText className="w-5 h-5" />
                </div>
                <span className="text-[11px] px-2.5 py-1 rounded-full bg-emerald-950/40 text-emerald-400 border border-emerald-500/30 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> {doc.status}
                </span>
              </div>

              <h3 className="text-base font-semibold text-white mt-4 group-hover:text-purple-300 transition-colors">
                {doc.title}
              </h3>
              <p className="text-xs text-purple-300/60 mt-1.5 leading-relaxed">
                {doc.description}
              </p>

              <div className="mt-4 flex flex-wrap gap-1.5">
                {doc.sections.map((sec, i) => (
                  <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/40">
                    {sec}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-purple-900/20 flex items-center justify-between text-xs text-purple-300/50">
              <span>{doc.fileSize} • Updated {doc.updatedAt}</span>
              <div className="flex items-center gap-2">
                <button className="p-2 hover:bg-purple-900/30 rounded-lg text-purple-300 hover:text-white transition-colors" title="Preview SOP">
                  <Eye className="w-4 h-4" />
                </button>
                <button className="p-2 hover:bg-purple-900/30 rounded-lg text-purple-300 hover:text-white transition-colors" title="Download SOP Specification">
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
