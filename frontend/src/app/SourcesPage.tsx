import React, { useState, useEffect } from "react";
import {
  Library,
  Search,
  ExternalLink,
  ShieldCheck,
  FileText,
  BookOpen,
  Filter,
  Loader2,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { sourceService, SourcesOverviewResponse, SourceDocument } from "@/services/sourceService";

export const SourcesPage: React.FC = () => {
  const [overview, setOverview] = useState<SourcesOverviewResponse | null>(null);
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [overviewRes, docsRes] = await Promise.all([
          sourceService.getOverview(),
          sourceService.getDocuments(),
        ]);
        setOverview(overviewRes);
        setDocuments(docsRes);
      } catch (err) {
        console.error("Failed to load source explorer data", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const filteredDocs = documents.filter((doc) => {
    const matchesCol = selectedCollection === "ALL" || doc.collection === selectedCollection;
    const matchesQuery =
      searchQuery.trim() === "" ||
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.key_provisions.some((p) => p.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCol && matchesQuery;
  });

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
          <Library className="w-6 h-6 text-emerald-600" />
          Authoritative Legal & Regulatory Source Explorer
        </h1>
        <p className="text-xs sm:text-sm text-slate-500">
          Verified primary legal corpus reconciling WIPO Lex, Official Gazettes, Ayush Pharmacopoeias, and International Treaties.
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
        </div>
      ) : (
        <>
          {/* Collections Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {overview?.collections.map((col) => (
              <Card
                key={col.id}
                onClick={() => setSelectedCollection(selectedCollection === col.id ? "ALL" : col.id)}
                className={`cursor-pointer transition-all hover:border-emerald-500 p-4 space-y-2 ${
                  selectedCollection === col.id
                    ? "border-emerald-600 bg-emerald-50/50 dark:bg-emerald-950/40 shadow-sm"
                    : "border-slate-200 dark:border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-[10px] uppercase font-mono">
                    {col.jurisdiction}
                  </Badge>
                  <BookOpen className="w-4 h-4 text-emerald-600" />
                </div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white line-clamp-1">
                  {col.name}
                </h3>
                <p className="text-xs text-slate-500 line-clamp-2">
                  {col.description}
                </p>
                <div className="text-[10px] text-slate-400 pt-1">
                  Auth: {col.official_authority}
                </div>
              </Card>
            ))}
          </div>

          {/* Search & Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between pt-2">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search provisions, acts, or treaties..."
                className="pl-9 text-xs"
              />
            </div>

            <div className="flex items-center gap-2 text-xs">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-500">Filter:</span>
              <button
                onClick={() => setSelectedCollection("ALL")}
                className={`px-2.5 py-1 rounded text-xs transition-colors ${
                  selectedCollection === "ALL"
                    ? "bg-emerald-800 text-white font-medium"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 hover:bg-slate-200"
                }`}
              >
                All ({documents.length})
              </button>
              {overview?.collections.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setSelectedCollection(c.id)}
                  className={`px-2.5 py-1 rounded text-xs transition-colors hidden sm:inline-block ${
                    selectedCollection === c.id
                      ? "bg-emerald-800 text-white font-medium"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {c.id.split("_")[0]}
                </button>
              ))}
            </div>
          </div>

          {/* Documents List */}
          <div className="space-y-3">
            {filteredDocs.map((doc) => (
              <Card key={doc.id} className="p-4 border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-[10px] font-mono">
                        {doc.document_type}
                      </Badge>
                      <Badge
                        variant="outline"
                        className="text-[10px] border-emerald-300 text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/40"
                      >
                        <ShieldCheck className="w-3 h-3 mr-1" />
                        {doc.verification_status}
                      </Badge>
                    </div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-1.5">
                      {doc.title}
                    </h3>
                  </div>

                  <a
                    href={doc.official_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-800 dark:text-emerald-400 shrink-0"
                  >
                    View Official Text <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                    Key Provisions & Monograph Sections:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {doc.key_provisions.map((prov, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center text-[11px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono"
                      >
                        <FileText className="w-3 h-3 mr-1 text-slate-400" />
                        {prov}
                      </span>
                    ))}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
