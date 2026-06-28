/**
 * MapPanel — React-Leaflet mapa de Valencia con rutas optimizadas
 * CRÍTICO: z-index: 9999 para overlay sobre capas Leaflet (que van hasta 650)
 */

import React, { useEffect, useRef } from "react";
import L from "leaflet";

// Datos de rutas: coordenadas reales de Valencia
const ROUTES = {
  before: [
    {
      id: "A",
      name: "El Carmen",
      color: "#e24b4a",
      type: "Diésel",
      paths: [
        [[39.4736, -0.3799], [39.4720, -0.3810], [39.4701, -0.3814], [39.4742, -0.3790]],
        [[39.4742, -0.3790], [39.4736, -0.3799]],
        [[39.4701, -0.3814], [39.4720, -0.3810], [39.4736, -0.3799]],
      ],
      dash: [8, 4],
    },
    {
      id: "B",
      name: "Ruzafa",
      color: "#eda100",
      type: "Híbrido",
      paths: [
        [[39.4622, -0.3738], [39.4615, -0.3742], [39.4630, -0.3750]],
        [[39.4630, -0.3750], [39.4622, -0.3738]],
      ],
      dash: [8, 4],
    },
    {
      id: "C",
      name: "Centro hist.",
      color: "#2a78d6",
      type: "EV",
      paths: [[[39.4742, -0.3790], [39.4760, -0.3780], [39.4780, -0.3770]]],
      dash: [8, 4],
    },
    {
      id: "D",
      name: "Benimaclet",
      color: "#639922",
      type: "EV",
      paths: [[[39.4834, -0.3627], [39.5030, -0.3628]]],
      dash: [8, 4],
    },
  ],
  after: [
    {
      id: "A-opt",
      name: "Ruta A consolidada",
      color: "#2a78d6",
      paths: [[[39.4736, -0.3799], [39.4701, -0.3814], [39.4742, -0.3790]]],
      dash: null,
    },
    {
      id: "B-opt",
      name: "Ruta B consolidada",
      color: "#1baf7a",
      paths: [[[39.4622, -0.3738], [39.4615, -0.3742]]],
      dash: null,
    },
    {
      id: "C-opt",
      name: "Ruta C EV",
      color: "#2a78d6",
      paths: [[[39.4742, -0.3790], [39.4780, -0.3770]]],
      dash: null,
    },
    {
      id: "D-opt",
      name: "Ruta D EV",
      color: "#639922",
      paths: [[[39.4834, -0.3627], [39.5030, -0.3628]]],
      dash: null,
    },
  ],
};

const ZONES = [
  { center: [39.4736, -0.3799], radius: 400, color: "#e24b4a", label: "El Carmen (vulnerable)", icon: "⚠️" },
  { center: [39.4622, -0.3738], radius: 350, color: "#eda100", label: "Ruzafa", icon: "🏫" },
  { center: [39.4742, -0.3790], radius: 300, color: "#2a78d6", label: "Centro hist. (escolar)", icon: "🏫" },
  { center: [39.4834, -0.3627], radius: 280, color: "#639922", label: "Benimaclet", icon: "✅" },
];

const HEAT_POINTS = [
  { center: [39.4701, -0.3814], radius: 520, intensity: "Alta", color: "#dc2626" },
  { center: [39.4664, -0.3761], radius: 460, intensity: "Alta", color: "#ef4444" },
  { center: [39.4739, -0.3652], radius: 420, intensity: "Media", color: "#f97316" },
  { center: [39.4865, -0.3688], radius: 380, intensity: "Media", color: "#f59e0b" },
  { center: [39.4588, -0.3564], radius: 320, intensity: "Baja", color: "#22c55e" },
];

export default function MapPanel({ activeRoute, optimized }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const layerGroup = useRef(null);

  useEffect(() => {
    // Inicializar mapa Leaflet
    if (!mapInstance.current && mapRef.current) {
      if (!L) return;

      const map = L.map(mapRef.current, {
        center: [39.4749, -0.3767], // Valencia centro
        zoom: 14,
        zoomControl: true,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap",
        maxZoom: 18,
      }).addTo(map);

      layerGroup.current = L.layerGroup().addTo(map);
      mapInstance.current = map;

      // Añadir zonas vulnerables
      ZONES.forEach((zone) => {
        L.circle(zone.center, {
          radius: zone.radius,
          color: zone.color,
          fillColor: zone.color,
          fillOpacity: 0.12,
          weight: 1.5,
          opacity: 0.5,
        }).addTo(map).bindTooltip(`${zone.icon} ${zone.label}`, { permanent: false });
      });

      // Capa térmica aproximada del reto: radios concéntricos por prioridad de calentamiento.
      HEAT_POINTS.forEach((point) => {
        L.circle(point.center, {
          radius: point.radius,
          color: point.color,
          fillColor: point.color,
          fillOpacity: 0.1,
          weight: 1,
          opacity: 0.35,
        }).addTo(map).bindTooltip(`Zona térmica ${point.intensity}`, { permanent: false });
      });
    }

    // Actualizar rutas según estado
    if (layerGroup.current && mapInstance.current) {
      layerGroup.current.clearLayers();

      const routes = optimized ? ROUTES.after : ROUTES.before;
      routes.forEach((route) => {
        route.paths.forEach((path) => {
          const polyline = L.polyline(path, {
            color: route.color,
            weight: optimized ? 3 : 2,
            opacity: 0.9,
            dashArray: route.dash ? route.dash.join(",") : null,
          });
          polyline.bindTooltip(route.name);
          layerGroup.current.addLayer(polyline);
        });
      });
    }
  }, [optimized, activeRoute]);

  return (
    <div style={{ position: "relative", height: "100%", minHeight: 420 }}>
      {/* CRÍTICO: z-index 9999 sobre capas Leaflet (máximo z-index: 650) */}
      <div
        ref={mapRef}
        style={{ width: "100%", height: "100%", minHeight: 420 }}
        aria-label="Mapa de Valencia con rutas de entrega optimizadas"
        role="application"
      />
      <div
        style={{
          position: "absolute",
          top: 12,
          right: 12,
          zIndex: 9999,
          background: "var(--surface-2, #fff)",
          border: "0.5px solid var(--border, #ddd)",
          borderRadius: 8,
          padding: "10px 12px",
          minWidth: 160,
          fontSize: 11,
        }}
      >
        <div style={{ fontWeight: 500, marginBottom: 6 }}>
          {optimized ? "✓ Rutas ALBA optimizadas" : "⚠ Rutas sin optimizar"}
        </div>
        <div style={{ color: "var(--text-muted, #888)" }}>
          {optimized ? "66 km · −36% · −74% CO₂" : "103 km · 3 furgonetas duplicadas"}
        </div>
        <div style={{ marginTop: 6, color: "var(--text-muted, #888)" }}>
          {optimized ? "Clarke-Wright Savings VRP ✓" : "Sin consolidación"}
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          bottom: 12,
          left: 12,
          zIndex: 9999,
          background: "rgba(255,255,255,0.9)",
          border: "0.5px solid var(--border, #ddd)",
          borderRadius: 8,
          padding: "8px 10px",
          fontSize: 11,
          minWidth: 180,
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: 5 }}>Mapa térmico operativo</div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ color: "#dc2626" }}>●</span> Alta prioridad calor</div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ color: "#f59e0b" }}>●</span> Prioridad media</div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ color: "#22c55e" }}>●</span> Prioridad baja</div>
      </div>
    </div>
  );
}
