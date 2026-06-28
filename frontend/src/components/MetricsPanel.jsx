import React from "react";

export default function MetricsPanel({ metrics, optimized, expanded }) {
  const data = metrics || {
    distance_before_km: 103,
    distance_after_km: 66,
    co2_before_kg: 15.8,
    co2_after_kg: 4.1,
  };

  return (
    <div className="metrics-card">
      <div className="metric-row">
        <span>Distancia</span>
        <strong>{data.distance_before_km} → {data.distance_after_km} km</strong>
      </div>
      <div className="metric-row">
        <span>CO₂</span>
        <strong>{data.co2_before_kg} → {data.co2_after_kg} kg</strong>
      </div>
      <div className="metric-row">
        <span>Estado</span>
        <strong>{optimized ? "Optimizado" : "Demo base"}</strong>
      </div>
      {expanded ? (
        <p className="hint">
          Escenario Valencia con consolidación de rutas y cambio modal EV/híbrido.
        </p>
      ) : null}
    </div>
  );
}
