/**
 * MapPanel — selección dinámica Leaflet para ECOFLUX.
 */

import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";

const VALENCIA_CENTER = [39.4749, -0.3767];
const routeCache = new Map();

const HEATMAPS = {
  traffic: {
    label: "Mostrar mapa de calor de tráfico",
    color: "#ff5050",
    points: [
      [39.4699, -0.3763, 420],
      [39.4737, -0.3794, 360],
      [39.4668, -0.3712, 330],
      [39.4812, -0.3659, 300],
    ],
  },
  demand: {
    label: "Mostrar mapa de calor de demanda logística",
    color: "#8ebdce",
    points: [
      [39.4622, -0.3738, 380],
      [39.4768, -0.3816, 340],
      [39.4708, -0.3629, 310],
      [39.4542, -0.3361, 360],
    ],
  },
  emissions: {
    label: "Mostrar mapa de calor de emisiones",
    color: "#024ad8",
    points: [
      [39.4701, -0.3814, 430],
      [39.4865, -0.3688, 350],
      [39.4588, -0.3564, 300],
      [39.4742, -0.3790, 280],
    ],
  },
};

function icon(label, type) {
  return L.divIcon({
    className: `dynamic-marker dynamic-marker--${type}`,
    html: `<span>${label}</span>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  });
}

async function roadRoute(points) {
  if (!points?.length || points.length < 2) return { points: [], approximate: false };
  const key = points.map((point) => `${point.lon},${point.lat}`).join(";");

  if (!routeCache.has(key)) {
    routeCache.set(
      key,
      fetch(`https://router.project-osrm.org/route/v1/driving/${key}?overview=full&geometries=geojson`)
        .then((res) => (res.ok ? res.json() : Promise.reject()))
        .then((data) => {
          const coordinates = data.routes?.[0]?.geometry?.coordinates;
          if (!coordinates?.length) throw new Error("Sin geometría OSRM");
          return {
            points: coordinates.map(([lon, lat]) => ({ lat, lon })),
            approximate: false,
          };
        })
        .catch(() => ({ points, approximate: true })),
    );
  }

  return routeCache.get(key);
}

export default function MapPanel({
  mapMode,
  loadingPoint,
  unloadingPoint,
  waypoints,
  originalRoute,
  optimizedRoute,
  onMapPoint,
  canSelectPoints,
  reloadLabel = "Manual",
  lastUpdated,
  isReloading,
}) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const layerGroup = useRef(null);
  const [heatLayers, setHeatLayers] = useState({ traffic: false, demand: false, emissions: false });
  const [routes, setRoutes] = useState({ original: null, optimized: null });

  useEffect(() => {
    if (!mapInstance.current && mapRef.current) {
      const map = L.map(mapRef.current, {
        center: VALENCIA_CENTER,
        zoom: 13,
        zoomControl: true,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap",
        maxZoom: 18,
      }).addTo(map);

      layerGroup.current = L.layerGroup().addTo(map);
      mapInstance.current = map;
    }
  }, []);

  useEffect(() => {
    const map = mapInstance.current;
    if (!map) return undefined;

    const handleClick = (event) => {
      if (canSelectPoints && mapMode !== "none") onMapPoint(event.latlng);
    };

    map.on("click", handleClick);
    return () => map.off("click", handleClick);
  }, [canSelectPoints, mapMode, onMapPoint]);

  useEffect(() => {
    let cancelled = false;
    Promise.all([roadRoute(originalRoute), roadRoute(optimizedRoute)]).then(([original, optimized]) => {
      if (!cancelled) setRoutes({ original, optimized });
    });
    return () => {
      cancelled = true;
    };
  }, [originalRoute, optimizedRoute]);

  useEffect(() => {
    if (!layerGroup.current) return;
    layerGroup.current.clearLayers();

    Object.entries(HEATMAPS).forEach(([key, config]) => {
      if (!heatLayers[key]) return;
      config.points.forEach(([lat, lon, radius]) => {
        L.circle([lat, lon], {
          radius,
          color: config.color,
          fillColor: config.color,
          fillOpacity: 0.12,
          opacity: 0.22,
          weight: 1,
          interactive: false,
        }).addTo(layerGroup.current);
      });
    });

    if (routes.original?.points.length > 1) {
      L.polyline(routes.original.points.map((point) => [point.lat, point.lon]), {
        color: "#ff5050",
        weight: 4,
        opacity: routes.original.approximate ? 0.45 : 0.82,
        dashArray: routes.original.approximate ? "2,8" : "6,6",
        lineCap: "round",
        lineJoin: "round",
      }).addTo(layerGroup.current).bindTooltip(routes.original.approximate ? "Rutas originales aproximadas" : "Rutas originales");
    }

    if (routes.optimized?.points.length > 1) {
      L.polyline(routes.optimized.points.map((point) => [point.lat, point.lon]), {
        color: "#296ef9",
        weight: 5,
        opacity: routes.optimized.approximate ? 0.55 : 0.85,
        dashArray: routes.optimized.approximate ? "2,8" : null,
        lineCap: "round",
        lineJoin: "round",
      }).addTo(layerGroup.current).bindTooltip(routes.optimized.approximate ? "Rutas optimizadas aproximadas" : "Rutas optimizadas");
    }

    if (loadingPoint) {
      L.marker([loadingPoint.lat, loadingPoint.lon], { icon: icon("C", "loading") })
        .addTo(layerGroup.current)
        .bindTooltip("Punto de carga");
    }

    if (unloadingPoint) {
      L.marker([unloadingPoint.lat, unloadingPoint.lon], { icon: icon("D", "unloading") })
        .addTo(layerGroup.current)
        .bindTooltip("Punto de descarga");
    }

    waypoints.forEach((point, index) => {
      L.marker([point.lat, point.lon], { icon: icon(index + 1, "waypoint") })
        .addTo(layerGroup.current)
        .bindTooltip(`Waypoint ${index + 1}`);
    });
  }, [heatLayers, loadingPoint, routes, unloadingPoint, waypoints]);

  const updatedAt = lastUpdated
    ? new Intl.DateTimeFormat("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(lastUpdated)
    : "--:--:--";

  return (
    <div className="dynamic-map-wrap">
      <div
        ref={mapRef}
        className="dynamic-map"
        aria-label="Mapa dinámico de selección de puntos de entrega"
        role="application"
      />
      <div className={`map-reload-status ${isReloading ? "map-reload-status--loading" : ""}`}>
        <strong>Recarga en tiempo real</strong>
        <span>{reloadLabel === "Manual" ? "Modo manual" : reloadLabel}</span>
        <span>Última actualización: {updatedAt}</span>
      </div>
      <div className="map-layers">
        <strong>Capas</strong>
        {Object.entries(HEATMAPS).map(([key, config]) => (
          <label key={key}>
            <input
              type="checkbox"
              checked={heatLayers[key]}
              onChange={(event) => setHeatLayers({ ...heatLayers, [key]: event.target.checked })}
            />
            {config.label}
          </label>
        ))}
      </div>
      <div className="map-legend">
        <strong>{canSelectPoints && mapMode !== "none" ? "Modo activo" : "Selección inactiva"}</strong>
        <span>Original: rojo · Optimizada: azul</span>
        {(routes.original?.approximate || routes.optimized?.approximate) ? <span>Ruta aproximada: línea punteada fina</span> : null}
      </div>
    </div>
  );
}
