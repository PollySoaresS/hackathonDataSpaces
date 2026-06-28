/**
 * API client GIS — ALBA data_IA
 * Conecta con /api/gis/* del backend FastAPI.
 */

const BASE_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) ||
  (typeof window !== "undefined"
    ? `http://${window.location.hostname}:8000`
    : "http://localhost:8000");

/**
 * Catálogo de capas WMS + WMTS disponibles en ICV.
 * @returns {{ wms_layers: Array, wmts_layers: Array }}
 */
export async function fetchGisCatalog() {
  const resp = await fetch(`${BASE_URL}/api/gis/catalog`);
  if (!resp.ok) throw new Error(`GIS catalog error: ${resp.status}`);
  return resp.json();
}

/**
 * Consulta WFS vectorial (datos analíticos).
 * @param {string} typeName  - Nombre de capa, p.e. "ICV:municipios_cv"
 * @param {string|null} bbox - "minx,miny,maxx,maxy" o null
 * @param {number} maxFeatures
 * @param {string} srsName
 * @returns {Promise<GeoJSON.FeatureCollection>}
 */
export async function fetchWfsFeatures(
  typeName,
  bbox = null,
  maxFeatures = 200,
  srsName = "EPSG:4326"
) {
  const params = new URLSearchParams({
    type_name: typeName,
    max_features: String(maxFeatures),
    srs_name: srsName,
  });
  if (bbox) params.set("bbox", bbox);
  const resp = await fetch(`${BASE_URL}/api/gis/wfs/features?${params}`);
  if (!resp.ok) throw new Error(`WFS error: ${resp.status}`);
  return resp.json();
}

/**
 * URL del proxy WMS backend (para OpenLayers TileWMS).
 * Incluye los parámetros como query string; el backend reenvía al ICV.
 */
export function getWmsProxyUrl() {
  return `${BASE_URL}/api/gis/wms/proxy`;
}
