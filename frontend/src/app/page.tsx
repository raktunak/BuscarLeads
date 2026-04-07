"use client";

import { useEffect, useState } from "react";
import { getCampaigns, getVerticals, getRegions, createCampaign, getLeads, getDashboardStats, downloadExport } from "@/lib/api";
import { login, register } from "@/lib/api";

type View = "login" | "dashboard" | "campaigns" | "leads";

export default function Home() {
  const [view, setView] = useState<View>("login");
  const [user, setUser] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [leads, setLeads] = useState<any[]>([]);
  const [leadsTotal, setLeadsTotal] = useState(0);
  const [verticals, setVerticals] = useState<any[]>([]);
  const [regions, setRegions] = useState<any[]>([]);
  const [selectedVertical, setSelectedVertical] = useState("");
  const [selectedRegion, setSelectedRegion] = useState("");
  const [selectedCampaign, setSelectedCampaign] = useState("");
  const [leadsPage, setLeadsPage] = useState(1);
  const [filters, setFilters] = useState({ website_status: "", min_score: "", search: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Auth form
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [isRegister, setIsRegister] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      setView("dashboard");
      loadDashboard();
    }
  }, []);

  async function handleAuth(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const data = isRegister
        ? await register(email, name, password)
        : await login(email, password);
      setUser(data);
      setView("dashboard");
      loadDashboard();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function loadDashboard() {
    try {
      const [s, c, v, r] = await Promise.all([
        getDashboardStats(),
        getCampaigns(),
        getVerticals(),
        getRegions(),
      ]);
      setStats(s);
      setCampaigns(c.campaigns);
      setVerticals(v);
      setRegions(r);
    } catch (err: any) {
      if (err.message.includes("Token") || err.message.includes("401")) {
        localStorage.removeItem("token");
        setView("login");
      }
    }
  }

  async function handleCreateCampaign() {
    if (!selectedVertical || !selectedRegion) return;
    setLoading(true);
    try {
      await createCampaign(selectedVertical, selectedRegion);
      const c = await getCampaigns();
      setCampaigns(c.campaigns);
      setSelectedVertical("");
      setSelectedRegion("");
    } catch (err: any) {
      setError(err.message);
    }
    setLoading(false);
  }

  async function loadLeads(campaignId?: string, page = 1) {
    setLoading(true);
    try {
      const params: any = { page, per_page: 50, ...filters };
      if (campaignId) params.campaign_id = campaignId;
      if (filters.min_score) params.min_score = parseInt(filters.min_score);
      const data = await getLeads(params);
      setLeads(data.leads);
      setLeadsTotal(data.total);
      setLeadsPage(page);
    } catch (err: any) {
      setError(err.message);
    }
    setLoading(false);
  }

  function logout() {
    localStorage.removeItem("token");
    setUser(null);
    setView("login");
  }

  // Login screen
  if (view === "login") {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-full max-w-sm p-8 bg-zinc-900 rounded-xl border border-zinc-800">
          <h1 className="text-2xl font-bold text-brand-500 mb-6">VenderWEB</h1>
          <form onSubmit={handleAuth} className="space-y-4">
            {isRegister && (
              <input
                type="text" placeholder="Nombre" value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
              />
            )}
            <input
              type="email" placeholder="Email" value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
            />
            <input
              type="password" placeholder="Password" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
            />
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <button type="submit" className="w-full py-2 bg-brand-500 text-black font-bold rounded-lg hover:bg-brand-400">
              {isRegister ? "Crear cuenta" : "Entrar"}
            </button>
            <button type="button" onClick={() => setIsRegister(!isRegister)} className="w-full text-sm text-zinc-400 hover:text-brand-500">
              {isRegister ? "Ya tengo cuenta" : "Crear cuenta nueva"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <nav className="w-56 bg-zinc-950 border-r border-zinc-800 flex flex-col">
        <div className="p-4 border-b border-zinc-800">
          <h2 className="text-sm font-bold text-brand-500 tracking-widest uppercase">VenderWEB</h2>
          <p className="text-xs text-zinc-500 mt-1">Lead Generation</p>
        </div>
        <div className="flex-1 p-2 space-y-1">
          {[
            { id: "dashboard", label: "Dashboard" },
            { id: "campaigns", label: "Campanas" },
            { id: "leads", label: "Leads" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setView(item.id as View);
                if (item.id === "dashboard") loadDashboard();
                if (item.id === "leads") loadLeads(selectedCampaign);
              }}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                view === item.id ? "bg-brand-500/10 text-brand-500 font-semibold" : "text-zinc-400 hover:text-white"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="p-4 border-t border-zinc-800">
          <button onClick={logout} className="text-xs text-zinc-500 hover:text-red-400">Cerrar sesion</button>
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-8">
        {/* DASHBOARD */}
        {view === "dashboard" && stats && (
          <div>
            <h1 className="text-3xl font-bold text-white mb-8">Dashboard</h1>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              {[
                { label: "Total Leads", value: stats.total_leads },
                { label: "Sin Web", value: stats.leads_no_web },
                { label: "Con Telefono", value: stats.leads_with_phone },
                { label: "Score Medio", value: stats.avg_lead_score },
              ].map((s) => (
                <div key={s.label} className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
                  <div className="text-2xl font-bold text-brand-500">{s.value}</div>
                  <div className="text-xs text-zinc-500 mt-1 uppercase tracking-wider">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Web status breakdown */}
            {stats.leads_by_status && Object.keys(stats.leads_by_status).length > 0 && (
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 mb-8">
                <h3 className="text-sm font-semibold text-white mb-3">Estado Web</h3>
                <div className="flex gap-4 flex-wrap">
                  {Object.entries(stats.leads_by_status).map(([status, count]) => (
                    <div key={status} className="text-center">
                      <div className="text-lg font-bold text-white">{count as number}</div>
                      <div className="text-xs text-zinc-500">{status}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* CAMPAIGNS */}
        {view === "campaigns" && (
          <div>
            <h1 className="text-3xl font-bold text-white mb-8">Campanas</h1>

            {/* New campaign form */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 mb-8">
              <h3 className="text-sm font-semibold text-white mb-4">Nueva Campana</h3>
              <div className="flex gap-4 items-end flex-wrap">
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">Vertical</label>
                  <select
                    value={selectedVertical}
                    onChange={(e) => setSelectedVertical(e.target.value)}
                    className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm min-w-[200px]"
                  >
                    <option value="">Seleccionar...</option>
                    {verticals.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.icon} {v.display_name?.es || v.slug}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">Region</label>
                  <select
                    value={selectedRegion}
                    onChange={(e) => setSelectedRegion(e.target.value)}
                    className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm min-w-[200px]"
                  >
                    <option value="">Seleccionar...</option>
                    {regions.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name} ({r.country_code})
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={handleCreateCampaign}
                  disabled={loading || !selectedVertical || !selectedRegion}
                  className="px-6 py-2 bg-brand-500 text-black font-bold rounded-lg hover:bg-brand-400 disabled:opacity-50"
                >
                  {loading ? "Creando..." : "Lanzar"}
                </button>
              </div>
            </div>

            {/* Campaign list */}
            <div className="space-y-3">
              {campaigns.map((c) => (
                <div key={c.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-white">{c.vertical_name} - {c.region_name}</div>
                    <div className="text-xs text-zinc-500 mt-1">
                      {c.total_found} encontrados | {c.total_qualified} nuevos |{" "}
                      <span className={c.status === "completed" ? "text-green-400" : c.status === "running" ? "text-brand-500" : c.status === "failed" ? "text-red-400" : "text-zinc-400"}>
                        {c.status}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedCampaign(c.id);
                      setView("leads");
                      loadLeads(c.id);
                    }}
                    className="px-4 py-1.5 border border-brand-500 text-brand-500 rounded-lg text-sm hover:bg-brand-500/10"
                  >
                    Ver leads
                  </button>
                </div>
              ))}
              {campaigns.length === 0 && (
                <p className="text-zinc-500 text-sm">No hay campanas todavia. Crea una arriba.</p>
              )}
            </div>
          </div>
        )}

        {/* LEADS */}
        {view === "leads" && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-3xl font-bold text-white">Leads</h1>
              <div className="flex gap-2">
                <button
                  onClick={() => downloadExport("csv", { campaign_id: selectedCampaign, ...filters })}
                  className="px-4 py-1.5 border border-zinc-700 text-zinc-300 rounded-lg text-sm hover:border-brand-500"
                >
                  CSV
                </button>
                <button
                  onClick={() => downloadExport("excel", { campaign_id: selectedCampaign, ...filters })}
                  className="px-4 py-1.5 bg-brand-500 text-black font-semibold rounded-lg text-sm hover:bg-brand-400"
                >
                  Excel
                </button>
              </div>
            </div>

            {/* Filters */}
            <div className="flex gap-3 mb-6 flex-wrap">
              <input
                placeholder="Buscar nombre..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-white w-48"
              />
              <select
                value={filters.website_status}
                onChange={(e) => setFilters({ ...filters, website_status: e.target.value })}
                className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-white"
              >
                <option value="">Todos los estados web</option>
                <option value="none">Sin web</option>
                <option value="dead">Web caida</option>
                <option value="parked">Dominio aparcado</option>
                <option value="basic">Web basica</option>
                <option value="professional">Web profesional</option>
              </select>
              <input
                type="number" placeholder="Score minimo"
                value={filters.min_score}
                onChange={(e) => setFilters({ ...filters, min_score: e.target.value })}
                className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-white w-32"
              />
              <button
                onClick={() => loadLeads(selectedCampaign)}
                className="px-4 py-1.5 bg-brand-500 text-black font-semibold rounded-lg text-sm"
              >
                Filtrar
              </button>
              <span className="text-sm text-zinc-500 self-center">{leadsTotal} resultados</span>
            </div>

            {/* Leads table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-brand-500">
                    {["Score", "Nombre", "Telefono", "Ciudad", "Web", "Estado", "Rating", "Resenas"].map((h) => (
                      <th key={h} className="px-3 py-2 text-left text-xs font-bold text-brand-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {leads.map((lead) => (
                    <tr key={lead.id} className="border-b border-zinc-800 hover:bg-zinc-900/50">
                      <td className="px-3 py-2">
                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${
                          lead.lead_score >= 60 ? "bg-green-900/50 text-green-400" :
                          lead.lead_score >= 30 ? "bg-yellow-900/50 text-yellow-400" :
                          "bg-zinc-800 text-zinc-400"
                        }`}>
                          {lead.lead_score}
                        </span>
                      </td>
                      <td className="px-3 py-2 font-medium text-white">{lead.name}</td>
                      <td className="px-3 py-2 font-mono text-xs">{lead.phone || "-"}</td>
                      <td className="px-3 py-2">{lead.city || "-"}</td>
                      <td className="px-3 py-2 text-xs">
                        {lead.website_url ? (
                          <a href={lead.website_url} target="_blank" rel="noopener" className="text-brand-500 hover:underline truncate block max-w-[200px]">
                            {lead.website_url.replace(/https?:\/\//, "").slice(0, 30)}
                          </a>
                        ) : (
                          <span className="text-red-400">Sin web</span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <span className={`text-xs ${
                          lead.website_status === "none" ? "text-red-400" :
                          lead.website_status === "dead" ? "text-red-400" :
                          lead.website_status === "professional" ? "text-green-400" :
                          "text-yellow-400"
                        }`}>
                          {lead.website_status || "?"}
                        </span>
                      </td>
                      <td className="px-3 py-2">{lead.google_rating || "-"}</td>
                      <td className="px-3 py-2">{lead.google_reviews || "-"}</td>
                    </tr>
                  ))}
                  {leads.length === 0 && (
                    <tr><td colSpan={8} className="px-3 py-8 text-center text-zinc-500">
                      {loading ? "Cargando..." : "No hay leads. Lanza una campana primero."}
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {leadsTotal > 50 && (
              <div className="flex gap-2 mt-4 justify-center">
                <button
                  disabled={leadsPage <= 1}
                  onClick={() => loadLeads(selectedCampaign, leadsPage - 1)}
                  className="px-3 py-1 border border-zinc-700 rounded text-sm disabled:opacity-30"
                >
                  Anterior
                </button>
                <span className="px-3 py-1 text-sm text-zinc-400">
                  Pagina {leadsPage} de {Math.ceil(leadsTotal / 50)}
                </span>
                <button
                  disabled={leadsPage >= Math.ceil(leadsTotal / 50)}
                  onClick={() => loadLeads(selectedCampaign, leadsPage + 1)}
                  className="px-3 py-1 border border-zinc-700 rounded text-sm disabled:opacity-30"
                >
                  Siguiente
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
