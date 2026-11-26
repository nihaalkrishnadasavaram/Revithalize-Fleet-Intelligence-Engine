const API_BASE = import.meta.env.VITE_API_URL ?? "";

function buildQueryString(parameters = {}) {
  const query = new URLSearchParams();
  Object.entries(parameters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  const text = query.toString();
  return text ? `?${text}` : "";
}

async function readErrorMessage(response) {
  const fallback = `The server responded with status ${response.status}.`;
  try {
    const body = await response.json();
    return typeof body.detail === "string" ? body.detail : fallback;
  } catch {
    return fallback;
  }
}

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch {
    throw new Error(
      "Cannot reach the RFIE backend. Make sure it is running at http://127.0.0.1:8000."
    );
  }
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json();
}

export const getHealth = () => request("/api/health");

export const getSummary = () => request("/api/dashboard/summary");

export const getVehicles = (parameters) => request(`/api/vehicles${buildQueryString(parameters)}`);

export const getVehicle = (vehicleId) => request(`/api/vehicles/${encodeURIComponent(vehicleId)}`);

export const getRecommendations = (parameters) =>
  request(`/api/recommendations${buildQueryString(parameters)}`);

export const getAlerts = (parameters) => request(`/api/alerts${buildQueryString(parameters)}`);

export const generateData = (parameters) =>
  request(`/api/data/generate${buildQueryString(parameters)}`, { method: "POST" });

export const exportUrl = `${API_BASE}/api/data/export`;
