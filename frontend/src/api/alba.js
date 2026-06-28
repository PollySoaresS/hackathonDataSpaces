/**
 * API client — ALBA data_IA
 * Conecta el frontend React con el backend FastAPI
 */

const browserHost = typeof window !== "undefined" ? window.location.hostname : "localhost";
const BASE_URL = import.meta.env.VITE_API_URL || `http://${browserHost}:8000`;

async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/** Métricas del demo Valencia */
export const fetchDemoMetrics = () => apiFetch("/api/optimize/demo");

/** Ejecutar optimización Clarke-Wright */
export const optimizeRoutes = (useDemo = true) =>
  apiFetch("/api/optimize/", {
    method: "POST",
    body: JSON.stringify({ use_demo: useDemo }),
  });

/** Anonimizar texto PHI */
export const anonymizeText = (
  text,
  model = "alia_groq_joint",
  deviceId = "alba-demo",
  scenario = "reto-empresas-valencia",
  companyType = "operador-urbano",
  strictMode = true,
) =>
  apiFetch("/api/anonymize/", {
    method: "POST",
    body: JSON.stringify({
      text,
      model,
      device_id: deviceId,
      scenario,
      company_type: companyType,
      strict_mode: strictMode,
    }),
  });

/** Proyección de impacto CO₂ */
export const fetchImpact = (operators = 2500) =>
  apiFetch(`/api/metrics/impact?operators=${operators}`);

/** Factores CO₂ EU Reg. 2019/1242 */
export const fetchCo2Factors = () => apiFetch("/api/metrics/co2-factors");

/** Health check */
export const healthCheck = () => apiFetch("/api/health");
