/**
 * GisMapPanel — ALBA data_IA
 * Panel "Mapa ICV" usando OpenLayers 10.
 *
 * Capas:
 *  - Base OSM (siempre visible)
 *  - Proxy WMS ICV (capa seleccionable del catálogo)
 *  - WFS vectorial ICV (GeoJSON superpuesto)
 *
 * NOTA: El mapa se centra en Valencia (EPSG:3857).
 */
import React, { useEffect, useRef, useState } from "react";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import OSM from "ol/source/OSM";
import TileWMS from "ol/source/TileWMS";
import VectorSource from "ol/source/Vector";
import GeoJSON from "ol/format/GeoJSON";
import { fromLonLat } from "ol/proj";
import { Style, Fill, Stroke } from "ol/style";
import "ol/ol.css";
import { fetchGisCatalog, fetchWfsFeatures, getWmsProxyUrl } from "../api/gis";

// Valencia centro (lon, lat) → EPSG:3857
const VALENCIA_CENTER = fromLonLat([-0.3763, 39.4699]);

const WFS_STYLE = new Style({
  fill: new Fill({ color: "rgba(0, 120, 200, 0.18)" }),
  stroke: new Stroke({ color: "#0078C8", width: 1.5 }),
});

export default function GisMapPanel() {
  const mapRef = useRef(null);
  const olMapRef = useRef(null);
  const wmsLayerRef = useRef(null);
  const wfsLayerRef = useRef(null);

  const [catalog, setCatalog] = useState({ wms_layers: [], wmts_layers: [] });
  const [selectedWms, setSelectedWms] = useState("");
  const [wfsTypeName, setWfsTypeName] = useState("");
  const [loadingWfs, setLoadingWfs] = useState(false);
  const [wfsError, setWfsError] = useState("");
  const [featureCount, setFeatureCount] = useState(null);

  // ── Init mapa ────────────────────────────────────────────────────────
  useEffect(() => {
    if (olMapRef.current) return;

    const osmBase = new TileLayer({ source: new OSM() });

    wmsLayerRef.current = new TileLayer({
      visible: false,
      source: new TileWMS({
        url: getWmsProxyUrl(),
        params: { LAYERS: "", FORMAT: "image/png", TRANSPARENT: "TRUE" },
        serverType: "geoserver",
      }),
    });

    const wfsSource = new VectorSource();
    wfsLayerRef.current = new VectorLayer({
      source: wfsSource,
      style: WFS_STYLE,
    });

    olMapRef.current = new Map({
      target: mapRef.current,
      layers: [osmBase, wmsLayerRef.current, wfsLayerRef.current],
      view: new View({ center: VALENCIA_CENTER, zoom: 11 }),
    });

    // Cargar catálogo (silencioso si no hay URLs ICV)
    fetchGisCatalog()
      .then(setCatalog)
      .catch(() => setCatalog({ wms_layers: [], wmts_layers: [] }));

    return () => {
      olMapRef.current?.setTarget(undefined);
      olMapRef.current = null;
    };
  }, []);

  // ── Cambio de capa WMS ────────────────────────────────────────────────
  function handleWmsChange(e) {
    const layerName = e.target.value;
    setSelectedWms(layerName);
    if (!wmsLayerRef.current) return;
    if (!layerName) {
      wmsLayerRef.current.setVisible(false);
      return;
    }
    wmsLayerRef.current.getSource().updateParams({ LAYERS: layerName });
    wmsLayerRef.current.setVisible(true);
  }

  // ── Consulta WFS ──────────────────────────────────────────────────────
  async function handleWfsLoad() {
    if (!wfsTypeName.trim()) return;
    setLoadingWfs(true);
    setWfsError("");
    setFeatureCount(null);
    try {
      const geojson = await fetchWfsFeatures(wfsTypeName.trim(), null, 500);
      const format = new GeoJSON();
      const features = format.readFeatures(geojson, {
        featureProjection: "EPSG:3857",
      });
      const src = wfsLayerRef.current.getSource();
      src.clear();
      src.addFeatures(features);
      setFeatureCount(features.length);
      if (features.length > 0) {
        olMapRef.current.getView().fit(src.getExtent(), {
          padding: [40, 40, 40, 40],
          maxZoom: 14,
        });
      }
    } catch (err) {
      setWfsError(String(err));
    } finally {
      setLoadingWfs(false);
    }
  }

  // ── Render ────────────────────────────────────────────────────────────
  const allWmsLayers = [
    ...catalog.wms_layers,
    ...catalog.wmts_layers,
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Controles */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
          padding: "8px 12px",
          background: "#1e293b",
          borderRadius: 6,
          alignItems: "center",
        }}
      >
        {/* WMS selector */}
        <label style={{ color: "#94a3b8", fontSize: 13 }}>Capa WMS:</label>
        <select
          value={selectedWms}
          onChange={handleWmsChange}
          style={{
            background: "#0f172a",
            color: "#e2e8f0",
            border: "1px solid #334155",
            borderRadius: 4,
            padding: "3px 8px",
            fontSize: 13,
            minWidth: 200,
          }}
        >
          <option value="">— Ninguna —</option>
          {allWmsLayers.map((l) => (
            <option key={l.name} value={l.name}>
              {l.title || l.name}
            </option>
          ))}
          {allWmsLayers.length === 0 && (
            <option disabled>Sin capas (configura ICV_WMS_URL)</option>
          )}
        </select>

        {/* WFS loader */}
        <label style={{ color: "#94a3b8", fontSize: 13 }}>WFS typeName:</label>
        <input
          type="text"
          value={wfsTypeName}
          onChange={(e) => setWfsTypeName(e.target.value)}
          placeholder="ICV:municipios_cv"
          style={{
            background: "#0f172a",
            color: "#e2e8f0",
            border: "1px solid #334155",
            borderRadius: 4,
            padding: "3px 8px",
            fontSize: 13,
            width: 200,
          }}
          onKeyDown={(e) => e.key === "Enter" && handleWfsLoad()}
        />
        <button
          onClick={handleWfsLoad}
          disabled={loadingWfs || !wfsTypeName.trim()}
          style={{
            background: "#0ea5e9",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            padding: "4px 14px",
            cursor: loadingWfs ? "wait" : "pointer",
            fontSize: 13,
          }}
        >
          {loadingWfs ? "Cargando…" : "Cargar WFS"}
        </button>

        {featureCount !== null && (
          <span style={{ color: "#4ade80", fontSize: 12 }}>
            {featureCount} entidades
          </span>
        )}
        {wfsError && (
          <span style={{ color: "#f87171", fontSize: 12 }}>{wfsError}</span>
        )}
      </div>

      {/* Mapa */}
      <div
        ref={mapRef}
        style={{ height: 480, borderRadius: 6, overflow: "hidden" }}
      />
    </div>
  );
}
