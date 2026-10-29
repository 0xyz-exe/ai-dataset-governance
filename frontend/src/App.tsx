import React, { useState, useEffect } from "react";
import {
  Database,
  GitBranch,
  ShieldCheck,
  GitFork,
  FileCode,
  Layers,
  HardDrive,
  Cpu,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Search,
  Plus,
  RefreshCw,
  ArrowRight,
  ChevronRight,
  Shield,
  Sparkles,
} from "lucide-react";

interface Dataset {
  id: string;
  name: string;
  slug: string;
  description: string;
  domain: string;
  task_type: string;
  license: string;
  visibility: string;
  quality_status: string;
  latest_version: string | null;
  total_versions: number;
  total_files: number;
  total_size_bytes: number;
  tags: string[];
  created_at: string;
}

interface OverviewStats {
  total_datasets: number;
  total_versions: number;
  total_blobs: number;
  total_storage_bytes: number;
  total_quality_runs: number;
  avg_quality_score: number;
  total_experiments: number;
  total_audit_events: number;
  quality_distribution: {
    passed: number;
    warning: number;
    failed: number;
    unverified: number;
  };
}

export default function App() {
  const [activeTab, setActiveTab] = useState<
    "overview" | "datasets" | "detail" | "compare" | "quality" | "provenance" | "schemas" | "experiments" | "governance"
  >("overview");
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const [activeDetailSubTab, setActiveDetailSubTab] = useState<"files" | "versions" | "quality" | "provenance" | "schemas">("files");
  const [searchQuery, setSearchQuery] = useState("");
  const [domainFilter, setDomainFilter] = useState("all");

  // Detail data states
  const [datasetFiles, setDatasetFiles] = useState<any[]>([]);
  const [datasetVersions, setDatasetVersions] = useState<any[]>([]);
  const [qualityRuns, setQualityRuns] = useState<any[]>([]);
  const [lineage, setLineage] = useState<any>(null);
  const [schemas, setSchemas] = useState<any[]>([]);
  const [experiments, setExperiments] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // Create dataset modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newDomain, setNewDomain] = useState("tabular");
  const [newLicense, setNewLicense] = useState("Apache-2.0");

  // Version compare selection
  const [compareBase, setCompareBase] = useState("");
  const [compareTarget, setCompareTarget] = useState("");
  const [compareResult, setCompareResult] = useState<any>(null);

  const fetchStats = async () => {
    try {
      const res = await fetch("/api/v1/overview/stats");
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.warn("Could not fetch remote stats", e);
    }
  };

  const fetchDatasets = async () => {
    try {
      const res = await fetch("/api/v1/datasets");
      if (res.ok) {
        const data = await res.json();
        setDatasets(data);
        if (!selectedDatasetId && data.length > 0) {
          setSelectedDatasetId(data[0].id);
        }
      }
    } catch (e) {
      console.warn("Could not fetch datasets", e);
    }
  };

  const fetchExperiments = async () => {
    try {
      const res = await fetch("/api/v1/experiments");
      if (res.ok) setExperiments(await res.json());
    } catch (e) {}
  };

  const fetchAuditLogs = async () => {
    try {
      const res = await fetch("/api/v1/governance/audit-logs");
      if (res.ok) setAuditLogs(await res.json());
    } catch (e) {}
  };

  const fetchDatasetDetails = async (id: string) => {
    try {
      const [fRes, vRes, qRes, pRes, sRes] = await Promise.all([
        fetch(`/api/v1/datasets/${id}/files`),
        fetch(`/api/v1/datasets/${id}/versions`),
        fetch(`/api/v1/datasets/${id}/quality/runs`),
        fetch(`/api/v1/datasets/${id}/provenance/lineage`),
        fetch(`/api/v1/datasets/${id}/schemas`),
      ]);
      if (fRes.ok) setDatasetFiles(await fRes.json());
      if (vRes.ok) {
        const vList = await vRes.json();
        setDatasetVersions(vList);
        if (vList.length >= 2) {
          setCompareBase(vList[1].id);
          setCompareTarget(vList[0].id);
        } else if (vList.length === 1) {
          setCompareBase(vList[0].id);
          setCompareTarget(vList[0].id);
        }
      }
      if (qRes.ok) setQualityRuns(await qRes.json());
      if (pRes.ok) setLineage(await pRes.json());
      if (sRes.ok) setSchemas(await sRes.json());
    } catch (e) {
      console.warn("Error fetching details", e);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchDatasets();
    fetchExperiments();
    fetchAuditLogs();
  }, []);

  useEffect(() => {
    if (selectedDatasetId) {
      fetchDatasetDetails(selectedDatasetId);
    }
  }, [selectedDatasetId]);

  const handleCreateDataset = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("/api/v1/datasets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newName,
          description: newDesc,
          domain: newDomain,
          license: newLicense,
          tags: [newDomain, "production"],
        }),
      });
      if (res.ok) {
        setShowCreateModal(false);
        setNewName("");
        setNewDesc("");
        fetchDatasets();
        fetchStats();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunCompare = async () => {
    if (!selectedDatasetId || !compareBase || !compareTarget) return;
    try {
      const res = await fetch(
        `/api/v1/datasets/${selectedDatasetId}/compare?base_version_id=${compareBase}&target_version_id=${compareTarget}`
      );
      if (res.ok) {
        setCompareResult(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId);

  const filteredDatasets = datasets.filter((d) => {
    const matchesDomain = domainFilter === "all" || d.domain === domainFilter;
    const matchesSearch =
      d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesDomain && matchesSearch;
  });

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="flex h-screen bg-[#090d16] text-slate-100 antialiased overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-[#0d131f] border-r border-slate-800/80 flex flex-col justify-between shrink-0">
        <div>
          {/* Logo & Tagline */}
          <div className="p-5 border-b border-slate-800/60">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <Database className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-sm tracking-wide text-white flex items-center gap-1.5">
                  Dataset Gov
                  <span className="text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded font-mono font-medium">v1.0</span>
                </h1>
                <p className="text-[11px] text-slate-400 font-medium">Version · Trace · Validate</p>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {[
              { id: "overview", label: "Overview Dashboard", icon: BarChart3 },
              { id: "datasets", label: "Dataset Registry", icon: Database },
              { id: "detail", label: "Dataset Explorer", icon: Layers },
              { id: "compare", label: "Version Comparison", icon: GitBranch },
              { id: "quality", label: "Quality & Gates", icon: ShieldCheck },
              { id: "provenance", label: "Provenance & Lineage", icon: GitFork },
              { id: "schemas", label: "Schema Registry", icon: FileCode },
              { id: "experiments", label: "ML Experiments", icon: Cpu },
              { id: "governance", label: "Governance & Audit", icon: Shield },
            ].map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as any)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-all cursor-pointer ${
                    isActive
                      ? "bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Storage Summary Footprint */}
        <div className="p-4 border-t border-slate-800/60 bg-[#090d16]/40">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
            <span className="flex items-center gap-1.5">
              <HardDrive className="w-3.5 h-3.5 text-slate-400" />
              Content-Addressed
            </span>
            <span className="font-mono text-[11px] text-slate-300">
              {stats ? formatBytes(stats.total_storage_bytes) : "..."}
            </span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full w-1/4 rounded-full"></div>
          </div>
          <div className="mt-2 text-[10px] text-slate-500 flex justify-between">
            <span>SHA-256 Blobs</span>
            <span className="font-mono">{stats?.total_blobs || 0} objects</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-[#090d16]">
        {/* Top Header Bar */}
        <header className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-[#0d131f]/50 backdrop-blur-sm shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold capitalize text-slate-200 tracking-wide flex items-center gap-2">
              {activeTab === "overview" && "System Telemetry & Activity"}
              {activeTab === "datasets" && "All Tracked Datasets"}
              {activeTab === "detail" && `Dataset: ${selectedDataset ? selectedDataset.name : "Explorer"}`}
              {activeTab === "compare" && "Version Diff Inspector"}
              {activeTab === "quality" && "Automated Quality Assurance & Gates"}
              {activeTab === "provenance" && "Artifact Lineage & DAG History"}
              {activeTab === "schemas" && "Data Schema Governance"}
              {activeTab === "experiments" && "ML Reproducibility & Model Runs"}
              {activeTab === "governance" && "Governance Policies & Audit Trail"}
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                fetchStats();
                fetchDatasets();
                if (selectedDatasetId) fetchDatasetDetails(selectedDatasetId);
              }}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 rounded-md transition-colors cursor-pointer"
              title="Refresh State"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-xs font-medium shadow-sm transition-all cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              New Dataset
            </button>
          </div>
        </header>

        {/* Tab Views */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* TAB 1: OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              {/* KPI Cards */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-4 shadow-sm">
                  <div className="flex items-center justify-between text-slate-400 text-xs">
                    <span>Registered Datasets</span>
                    <Database className="w-4 h-4 text-blue-400" />
                  </div>
                  <div className="text-2xl font-bold font-mono text-white mt-2">
                    {stats?.total_datasets ?? 0}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">Multi-modal AI assets</div>
                </div>

                <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-4 shadow-sm">
                  <div className="flex items-center justify-between text-slate-400 text-xs">
                    <span>Immutable Snapshots</span>
                    <GitBranch className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div className="text-2xl font-bold font-mono text-white mt-2">
                    {stats?.total_versions ?? 0}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">Cryptographically hashed</div>
                </div>

                <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-4 shadow-sm">
                  <div className="flex items-center justify-between text-slate-400 text-xs">
                    <span>Avg Quality Score</span>
                    <ShieldCheck className="w-4 h-4 text-indigo-400" />
                  </div>
                  <div className="text-2xl font-bold font-mono text-white mt-2">
                    {stats?.avg_quality_score ?? 0}%
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">Across automated suites</div>
                </div>

                <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-4 shadow-sm">
                  <div className="flex items-center justify-between text-slate-400 text-xs">
                    <span>Linked ML Models</span>
                    <Cpu className="w-4 h-4 text-amber-400" />
                  </div>
                  <div className="text-2xl font-bold font-mono text-white mt-2">
                    {stats?.total_experiments ?? 0}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">End-to-end reproducibility</div>
                </div>
              </div>

              {/* Quality Distribution & Storage Breakdown */}
              <div className="grid grid-cols-3 gap-6">
                <div className="col-span-2 bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                  <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
                    Dataset Quality Gate Status
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="flex items-center gap-1.5 text-emerald-400">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Passed Quality Gates
                        </span>
                        <span className="font-mono text-slate-300">{stats?.quality_distribution.passed || 0}</span>
                      </div>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-emerald-500 h-full rounded-full"
                          style={{
                            width: `${
                              ((stats?.quality_distribution.passed || 0) /
                                Math.max(1, stats?.total_versions || 1)) *
                              100
                            }%`,
                          }}
                        ></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="flex items-center gap-1.5 text-amber-400">
                          <AlertTriangle className="w-3.5 h-3.5" /> Warning / Review Required
                        </span>
                        <span className="font-mono text-slate-300">{stats?.quality_distribution.warning || 0}</span>
                      </div>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-amber-500 h-full rounded-full"
                          style={{
                            width: `${
                              ((stats?.quality_distribution.warning || 0) /
                                Math.max(1, stats?.total_versions || 1)) *
                              100
                            }%`,
                          }}
                        ></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="flex items-center gap-1.5 text-rose-400">
                          <XCircle className="w-3.5 h-3.5" /> Failed Integrity or Schema
                        </span>
                        <span className="font-mono text-slate-300">{stats?.quality_distribution.failed || 0}</span>
                      </div>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-rose-500 h-full rounded-full"
                          style={{
                            width: `${
                              ((stats?.quality_distribution.failed || 0) /
                                Math.max(1, stats?.total_versions || 1)) *
                              100
                            }%`,
                          }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5 flex flex-col justify-between">
                  <div>
                    <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                      Local Blob Engine
                    </h3>
                    <p className="text-xs text-slate-400 leading-relaxed mb-4">
                      Content-addressed storage model with zero duplicate binary payloads on disk.
                    </p>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between py-1 border-b border-slate-800">
                        <span className="text-slate-400">Hash Algorithm</span>
                        <span className="font-mono text-slate-200">SHA-256</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-800">
                        <span className="text-slate-400">Total Blobs</span>
                        <span className="font-mono text-slate-200">{stats?.total_blobs}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-800">
                        <span className="text-slate-400">Active Storage</span>
                        <span className="font-mono text-slate-200">
                          {stats ? formatBytes(stats.total_storage_bytes) : "0 B"}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="pt-3">
                    <button
                      onClick={() => setActiveTab("datasets")}
                      className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium rounded-md text-slate-200 flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                    >
                      Browse Datasets <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Recent Datasets Table */}
              <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Recent Ingested Datasets
                  </h3>
                  <button
                    onClick={() => setActiveTab("datasets")}
                    className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium cursor-pointer"
                  >
                    View All <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400">
                        <th className="pb-2 font-medium">Dataset Name</th>
                        <th className="pb-2 font-medium">Domain</th>
                        <th className="pb-2 font-medium">Latest Version</th>
                        <th className="pb-2 font-medium">Files</th>
                        <th className="pb-2 font-medium">Size</th>
                        <th className="pb-2 font-medium">Quality</th>
                        <th className="pb-2 text-right font-medium">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {datasets.slice(0, 5).map((d) => (
                        <tr key={d.id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-3 font-medium text-slate-200">
                            {d.name}
                            <div className="text-[10px] text-slate-500 font-mono">{d.slug}</div>
                          </td>
                          <td className="py-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300">
                              {d.domain}
                            </span>
                          </td>
                          <td className="py-3 font-mono text-slate-300">{d.latest_version || "—"}</td>
                          <td className="py-3 font-mono text-slate-400">{d.total_files}</td>
                          <td className="py-3 font-mono text-slate-400">{formatBytes(d.total_size_bytes)}</td>
                          <td className="py-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                                d.quality_status === "passed"
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                  : d.quality_status === "warning"
                                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                  : "bg-slate-800 text-slate-400"
                              }`}
                            >
                              {d.quality_status}
                            </span>
                          </td>
                          <td className="py-3 text-right">
                            <button
                              onClick={() => {
                                setSelectedDatasetId(d.id);
                                setActiveTab("detail");
                              }}
                              className="text-blue-400 hover:text-blue-300 font-medium text-xs inline-flex items-center gap-1 cursor-pointer"
                            >
                              Inspect <ChevronRight className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: DATASETS REGISTRY */}
          {activeTab === "datasets" && (
            <div className="space-y-4">
              {/* Filter and Search Bar */}
              <div className="flex items-center justify-between gap-4">
                <div className="relative flex-1 max-w-md">
                  <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by name, description, tags..."
                    className="w-full bg-[#0f172a] border border-slate-800 rounded-md pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Domain:</span>
                  <select
                    value={domainFilter}
                    onChange={(e) => setDomainFilter(e.target.value)}
                    className="bg-[#0f172a] border border-slate-800 rounded-md px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                  >
                    <option value="all">All Domains</option>
                    <option value="vision">Computer Vision</option>
                    <option value="tabular">Tabular</option>
                    <option value="nlp">Natural Language</option>
                  </select>
                </div>
              </div>

              {/* Dataset Cards Grid */}
              <div className="grid grid-cols-2 gap-4">
                {filteredDatasets.map((d) => (
                  <div
                    key={d.id}
                    className="bg-[#0f172a]/70 border border-slate-800/80 hover:border-slate-700 rounded-lg p-5 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div>
                          <h4 className="font-semibold text-sm text-white">{d.name}</h4>
                          <span className="font-mono text-[11px] text-slate-500">{d.id}</span>
                        </div>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-medium uppercase ${
                            d.quality_status === "passed"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : d.quality_status === "warning"
                              ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {d.quality_status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed mb-3">
                        {d.description || "No description provided."}
                      </p>
                      <div className="flex flex-wrap gap-1.5 mb-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                          {d.domain}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-400">
                          {d.license}
                        </span>
                        {d.tags?.slice(0, 3).map((t, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800/70 text-slate-400">
                            #{t}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-4 text-slate-400">
                        <span>
                          Version: <strong className="text-slate-200 font-mono">{d.latest_version || "—"}</strong>
                        </span>
                        <span>
                          Files: <strong className="text-slate-200 font-mono">{d.total_files}</strong>
                        </span>
                      </div>
                      <button
                        onClick={() => {
                          setSelectedDatasetId(d.id);
                          setActiveTab("detail");
                        }}
                        className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded transition-colors cursor-pointer"
                      >
                        Explore
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: DATASET DETAIL */}
          {activeTab === "detail" && selectedDataset && (
            <div className="space-y-6">
              {/* Dataset Header Card */}
              <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-6">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-lg font-bold text-white">{selectedDataset.name}</h3>
                    <p className="text-xs text-slate-400 mt-1 max-w-2xl">{selectedDataset.description}</p>
                  </div>
                  <div className="text-right">
                    <span className="px-2.5 py-1 rounded text-xs font-mono font-medium bg-blue-600/20 text-blue-400 border border-blue-500/30">
                      Latest: {selectedDataset.latest_version || "v1.0.0"}
                    </span>
                    <div className="text-[11px] text-slate-500 mt-1 font-mono">{selectedDataset.id}</div>
                  </div>
                </div>

                <div className="grid grid-cols-5 gap-4 pt-4 border-t border-slate-800 text-xs">
                  <div>
                    <span className="text-slate-500 block">Domain</span>
                    <strong className="text-slate-200 capitalize">{selectedDataset.domain}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Task Type</span>
                    <strong className="text-slate-200">{selectedDataset.task_type}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">License</span>
                    <strong className="text-slate-200">{selectedDataset.license}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Total Versions</span>
                    <strong className="text-slate-200 font-mono">{selectedDataset.total_versions}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Storage Footprint</span>
                    <strong className="text-slate-200 font-mono">{formatBytes(selectedDataset.total_size_bytes)}</strong>
                  </div>
                </div>
              </div>

              {/* Sub-tabs navigation */}
              <div className="border-b border-slate-800 flex gap-4">
                {[
                  { id: "files", label: "Files & Manifest", count: datasetFiles.length },
                  { id: "versions", label: "Version Snapshots", count: datasetVersions.length },
                  { id: "quality", label: "Quality Checks", count: qualityRuns.length },
                  { id: "provenance", label: "Lineage Graph", count: lineage?.nodes?.length || 0 },
                  { id: "schemas", label: "Schemas", count: schemas.length },
                ].map((st) => (
                  <button
                    key={st.id}
                    onClick={() => setActiveDetailSubTab(st.id as any)}
                    className={`pb-2.5 text-xs font-medium border-b-2 transition-all flex items-center gap-1.5 cursor-pointer ${
                      activeDetailSubTab === st.id
                        ? "border-blue-500 text-blue-400"
                        : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {st.label}
                    <span className="px-1.5 py-0.2 bg-slate-800 text-slate-400 text-[10px] rounded-full font-mono">
                      {st.count}
                    </span>
                  </button>
                ))}
              </div>

              {/* Sub-tab 1: Files */}
              {activeDetailSubTab === "files" && (
                <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                    Ingested Files & Blobs
                  </h4>
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400">
                        <th className="pb-2 font-medium">Logical Path</th>
                        <th className="pb-2 font-medium">Blob Digest (SHA-256)</th>
                        <th className="pb-2 font-medium">Size</th>
                        <th className="pb-2 font-medium">Integrity</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {datasetFiles.map((f) => (
                        <tr key={f.id} className="hover:bg-slate-800/30">
                          <td className="py-2.5 text-slate-200 font-sans">{f.logical_path}</td>
                          <td className="py-2.5 text-slate-400 text-[11px] truncate max-w-xs">{f.blob_hash}</td>
                          <td className="py-2.5 text-slate-300">{formatBytes(f.size_bytes)}</td>
                          <td className="py-2.5 text-emerald-400 text-[11px]">VERIFIED</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Sub-tab 2: Versions */}
              {activeDetailSubTab === "versions" && (
                <div className="space-y-4">
                  {datasetVersions.map((v) => (
                    <div key={v.id} className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-sm font-bold text-white bg-blue-600/20 text-blue-400 px-2 py-0.5 rounded border border-blue-500/30">
                            {v.semver}
                          </span>
                          <span className="text-xs text-slate-300 font-medium">{v.description}</span>
                        </div>
                        <span className="text-[11px] font-mono text-slate-500">{v.created_at}</span>
                      </div>
                      <div className="bg-[#090d16] p-3 rounded text-[11px] font-mono text-slate-400 space-y-1">
                        <div>
                          Manifest Hash: <span className="text-slate-300">{v.manifest_hash}</span>
                        </div>
                        <div>
                          Snapshot Files: <span className="text-slate-300">{v.files?.length || 0} file(s)</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Sub-tab 3: Quality */}
              {activeDetailSubTab === "quality" && (
                <div className="space-y-4">
                  {qualityRuns.map((qr) => (
                    <div key={qr.id} className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-bold text-white">Quality Run: {qr.id}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              qr.status === "passed"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            }`}
                          >
                            Score: {qr.overall_score}% ({qr.status})
                          </span>
                        </div>
                        <span className="text-xs text-slate-500">{qr.created_at}</span>
                      </div>
                      <div className="grid grid-cols-6 gap-2 mb-4">
                        {Object.entries(qr.dimension_scores || {}).map(([dim, score]: any) => (
                          <div key={dim} className="bg-[#090d16] p-2.5 rounded border border-slate-800 text-center">
                            <span className="text-[10px] text-slate-500 uppercase block truncate">{dim}</span>
                            <span className="font-mono text-xs font-bold text-slate-200">{score}%</span>
                          </div>
                        ))}
                      </div>
                      <div className="space-y-2">
                        {qr.checks?.map((chk: any, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-2 rounded bg-slate-900/40 text-xs border border-slate-800/40"
                          >
                            <span className="text-slate-300 flex items-center gap-2">
                              {chk.status === "passed" ? (
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                              ) : (
                                <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                              )}
                              {chk.message}
                            </span>
                            <span className="font-mono text-slate-400 uppercase text-[10px]">{chk.dimension}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Sub-tab 4: Provenance */}
              {activeDetailSubTab === "provenance" && (
                <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
                    Transformation Lineage Graph (DAG)
                  </h4>
                  <div className="space-y-3">
                    {lineage?.nodes?.map((node: any, idx: number) => (
                      <div
                        key={node.id}
                        className="p-3.5 bg-[#090d16] rounded-md border border-slate-800 flex items-center justify-between"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-7 h-7 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-mono text-xs font-bold">
                            {idx + 1}
                          </div>
                          <div>
                            <div className="font-medium text-xs text-white">{node.label}</div>
                            <div className="text-[10px] text-slate-500 font-mono">
                              Actor: {node.actor} · {node.created_at}
                            </div>
                          </div>
                        </div>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
                          {node.id}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sub-tab 5: Schemas */}
              {activeDetailSubTab === "schemas" && (
                <div className="space-y-4">
                  {schemas.map((s) => (
                    <div key={s.id} className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-xs font-bold text-white uppercase">{s.name} (v{s.version_num})</h4>
                        <span className="font-mono text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
                          {s.format_type}
                        </span>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs font-mono">
                          <thead>
                            <tr className="border-b border-slate-800 text-slate-400">
                              <th className="pb-1.5 font-sans font-medium">Field Name</th>
                              <th className="pb-1.5 font-sans font-medium">Type</th>
                              <th className="pb-1.5 font-sans font-medium">Required</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60 text-slate-300">
                            {s.schema_def?.fields?.map((f: any, idx: number) => (
                              <tr key={idx}>
                                <td className="py-1.5 text-blue-400">{f.name}</td>
                                <td className="py-1.5 text-slate-400">{f.type}</td>
                                <td className="py-1.5">{f.required ? "true" : "false"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: VERSION COMPARISON */}
          {activeTab === "compare" && (
            <div className="space-y-6">
              {/* Compare Selector Header */}
              <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
                  Select Snapshots to Compare
                </h3>
                <div className="grid grid-cols-3 gap-4 items-end">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Base Version</label>
                    <select
                      value={compareBase}
                      onChange={(e) => setCompareBase(e.target.value)}
                      className="w-full bg-[#090d16] border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-200"
                    >
                      {datasetVersions.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.semver} - {v.description}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Target Version</label>
                    <select
                      value={compareTarget}
                      onChange={(e) => setCompareTarget(e.target.value)}
                      className="w-full bg-[#090d16] border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-200"
                    >
                      {datasetVersions.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.semver} - {v.description}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    onClick={handleRunCompare}
                    className="py-1.5 px-4 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs rounded transition-colors cursor-pointer"
                  >
                    Run Differential Comparison
                  </button>
                </div>
              </div>

              {/* Comparison Results */}
              {compareResult && (
                <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5 space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-slate-300">
                        {compareResult.base_semver}
                      </span>
                      <ArrowRight className="w-4 h-4 text-slate-500" />
                      <span className="font-mono text-sm font-bold text-blue-400">
                        {compareResult.target_semver}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400">
                      Size delta: <strong className="text-slate-200 font-mono">{formatBytes(compareResult.size_delta_bytes)}</strong>
                    </div>
                  </div>

                  {/* Added / Modified / Removed summary */}
                  <div className="grid grid-cols-3 gap-4 text-xs font-medium">
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded text-emerald-400">
                      Added Files: {compareResult.added_files.length}
                    </div>
                    <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded text-amber-400">
                      Modified Files: {compareResult.modified_files.length}
                    </div>
                    <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded text-rose-400">
                      Removed Files: {compareResult.removed_files.length}
                    </div>
                  </div>

                  {/* Schema Changes list */}
                  <div>
                    <h4 className="text-xs font-semibold text-slate-300 uppercase mb-2">Detected Modifications</h4>
                    <ul className="space-y-1 text-xs text-slate-300">
                      {compareResult.schema_changes?.map((ch: string, idx: number) => (
                        <li key={idx} className="p-2 bg-[#090d16] rounded border border-slate-800 flex items-center gap-2">
                          <Sparkles className="w-3.5 h-3.5 text-blue-400" /> {ch}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: QUALITY & GATES */}
          {activeTab === "quality" && (
            <div className="space-y-6">
              <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Governance Quality Dimensions
                </h3>
                <p className="text-xs text-slate-400 mb-4 leading-relaxed">
                  Automatic static and semantic checks applied across Tabular, YOLO, and COCO formats with strict gate criteria.
                </p>

                <div className="grid grid-cols-3 gap-4 text-xs">
                  <div className="p-4 bg-[#090d16] border border-slate-800 rounded-md">
                    <div className="font-semibold text-white mb-1">Completeness & Nulls</div>
                    <p className="text-slate-400 text-[11px]">
                      Flags missing row entries, blank coordinates, and partial image-label pairs.
                    </p>
                  </div>
                  <div className="p-4 bg-[#090d16] border border-slate-800 rounded-md">
                    <div className="font-semibold text-white mb-1">Annotation Bounds [0, 1]</div>
                    <p className="text-slate-400 text-[11px]">
                      Verifies normalized YOLO bounding boxes and COCO segment structures.
                    </p>
                  </div>
                  <div className="p-4 bg-[#090d16] border border-slate-800 rounded-md">
                    <div className="font-semibold text-white mb-1">Cryptographic Integrity</div>
                    <p className="text-slate-400 text-[11px]">
                      Validates on-disk blob byte streams against manifest SHA-256 digests.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: PROVENANCE */}
          {activeTab === "provenance" && (
            <div className="space-y-4">
              <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
                  Provenance Lineage Tracking
                </h3>
                <p className="text-xs text-slate-400 mb-4">
                  Traces source data through transformations (filters, normalizations, image transforms) to versioned outputs.
                </p>
                <div className="space-y-2">
                  {lineage?.nodes?.map((node: any, idx: number) => (
                    <div key={idx} className="p-3 bg-[#090d16] border border-slate-800 rounded flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <GitFork className="w-4 h-4 text-blue-400" />
                        <span className="font-semibold text-xs text-white">{node.label}</span>
                      </div>
                      <span className="text-[11px] font-mono text-slate-400">Actor: {node.actor}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: SCHEMAS */}
          {activeTab === "schemas" && (
            <div className="space-y-4">
              <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
                  Registered Data Schemas
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {schemas.map((s) => (
                    <div key={s.id} className="p-4 bg-[#090d16] border border-slate-800 rounded">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-sm text-white">{s.name}</span>
                        <span className="text-xs font-mono bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
                          {s.format_type}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 font-mono">
                        {s.schema_def?.fields?.length || 0} columns/fields registered
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 8: EXPERIMENTS */}
          {activeTab === "experiments" && (
            <div className="space-y-4">
              <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
                  Model Reproducibility Runs
                </h3>
                <div className="space-y-3">
                  {experiments.map((exp) => (
                    <div key={exp.id} className="p-4 bg-[#090d16] border border-slate-800 rounded-lg space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="font-bold text-sm text-white">{exp.name}</h4>
                        <span className="font-mono text-xs bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded">
                          {exp.model_name} (v{exp.model_version})
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">{exp.description}</p>
                      <div className="flex items-center gap-6 pt-2 text-xs font-mono text-slate-300 border-t border-slate-800/80">
                        <div>Commit: <span className="text-blue-400">{exp.git_commit}</span></div>
                        <div>Framework: <span>{exp.framework}</span></div>
                        {exp.metrics && (
                          <div>
                            Metrics:{" "}
                            {Object.entries(exp.metrics).map(([k, v]: any) => (
                              <span key={k} className="mr-3 text-emerald-400 font-semibold">{k}={v}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 9: GOVERNANCE & AUDIT */}
          {activeTab === "governance" && (
            <div className="space-y-4">
              <div className="bg-[#0f172a]/70 border border-slate-800/80 rounded-lg p-5">
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
                  Append-Only Audit Log
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 font-sans">
                        <th className="pb-2 font-medium">Timestamp</th>
                        <th className="pb-2 font-medium">Actor</th>
                        <th className="pb-2 font-medium">Action</th>
                        <th className="pb-2 font-medium">Resource Type</th>
                        <th className="pb-2 font-medium">IP Address</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300">
                      {auditLogs.map((log) => (
                        <tr key={log.id} className="hover:bg-slate-800/30">
                          <td className="py-2 text-slate-500">{log.created_at}</td>
                          <td className="py-2 text-blue-400">{log.actor}</td>
                          <td className="py-2 font-semibold text-slate-200">{log.action}</td>
                          <td className="py-2 text-slate-400">{log.resource_type}</td>
                          <td className="py-2 text-slate-500">{log.ip_address}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Modal: Create Dataset */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#0f172a] border border-slate-800 rounded-lg max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-sm font-bold text-white mb-1">Create New Dataset</h3>
            <p className="text-xs text-slate-400 mb-4">Register an AI dataset for versioning and quality governance.</p>

            <form onSubmit={handleCreateDataset} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Dataset Name</label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Autonomous Driving LIDAR 3D"
                  className="w-full bg-[#090d16] border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Description</label>
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  rows={2}
                  placeholder="Task, sensors, provenance context..."
                  className="w-full bg-[#090d16] border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Domain</label>
                  <select
                    value={newDomain}
                    onChange={(e) => setNewDomain(e.target.value)}
                    className="w-full bg-[#090d16] border border-slate-800 rounded px-3 py-1.5 text-slate-200 focus:outline-none focus:border-blue-500"
                  >
                    <option value="tabular">Tabular</option>
                    <option value="vision">Computer Vision</option>
                    <option value="nlp">Natural Language</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">License</label>
                  <select
                    value={newLicense}
                    onChange={(e) => setNewLicense(e.target.value)}
                    className="w-full bg-[#090d16] border border-slate-800 rounded px-3 py-1.5 text-slate-200 focus:outline-none focus:border-blue-500"
                  >
                    <option value="Apache-2.0">Apache-2.0</option>
                    <option value="MIT">MIT</option>
                    <option value="CC-BY-4.0">CC-BY-4.0</option>
                    <option value="Proprietary">Proprietary</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-medium transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium transition-colors cursor-pointer"
                >
                  Register Dataset
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
