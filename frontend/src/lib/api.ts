const API_BASE = "/api";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function fetchApi<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

// Auth
export async function login(email: string, password: string) {
  const data = await fetchApi<{ access_token: string; user_id: string; name: string; role: string }>(
    "/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) }
  );
  localStorage.setItem("token", data.access_token);
  return data;
}

export async function register(email: string, name: string, password: string) {
  const data = await fetchApi<{ access_token: string; user_id: string; name: string; role: string }>(
    "/auth/register",
    { method: "POST", body: JSON.stringify({ email, name, password }) }
  );
  localStorage.setItem("token", data.access_token);
  return data;
}

// Catalog
export const getVerticals = () => fetchApi<any[]>("/catalog/verticals");
export const getRegions = (countryCode?: string) =>
  fetchApi<any[]>(`/catalog/regions${countryCode ? `?country_code=${countryCode}` : ""}`);

// Campaigns
export const getCampaigns = () => fetchApi<{ campaigns: any[]; total: number }>("/campaigns/");
export const createCampaign = (verticalId: string, regionId: string) =>
  fetchApi<any>("/campaigns/", {
    method: "POST",
    body: JSON.stringify({ vertical_id: verticalId, region_id: regionId }),
  });
export const getCampaign = (id: string) => fetchApi<any>(`/campaigns/${id}`);

// Leads
export const getLeads = (params: Record<string, any> = {}) => {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  });
  return fetchApi<{ leads: any[]; total: number; page: number; per_page: number }>(`/leads/?${qs}`);
};

// Dashboard
export const getDashboardStats = () => fetchApi<any>("/dashboard/stats");

// Exports
export function downloadExport(format: "csv" | "excel", params: Record<string, any> = {}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null) qs.set(k, String(v));
  });
  const token = getToken();
  const url = `${API_BASE}/exports/${format}?${qs}`;
  const a = document.createElement("a");
  // For authenticated downloads, use fetch + blob
  fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
    .then((r) => r.blob())
    .then((blob) => {
      a.href = URL.createObjectURL(blob);
      a.download = `leads.${format === "excel" ? "xlsx" : "csv"}`;
      a.click();
    });
}
