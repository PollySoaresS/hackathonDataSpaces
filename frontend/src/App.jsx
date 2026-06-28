/**
 * ALBA data_IA — Frontend React
 * Demostrador del optimizador de rutas con React-Leaflet + métricas CO₂
 * Stack: React + Vite + React-Leaflet + Recharts + tRPC
 */

import React, { useState, useEffect } from "react";
import MapPanel from "./components/MapPanel";
import MetricsPanel from "./components/MetricsPanel";
import RouteList from "./components/RouteList";
import GisMapPanel from "./components/GisMapPanel";
import { fetchDemoMetrics, optimizeRoutes } from "./api/alba";
import "./styles/app.css";

const TABS = ["Mapa urbano", "Mapa ICV", "Métricas CO₂"];

export default function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [activeRoute, setActiveRoute] = useState(0);
  const [optimized, setOptimized] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDemoMetrics().then(setMetrics).catch(console.error);
  }, []);

  const handleOptimize = async () => {
    setLoading(true);
    try {
      await optimizeRoutes(true);
      setOptimized(true);
    } catch {
      setOptimized(true); // Demo funciona offline
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setOptimized(false);
    setActiveRoute(0);
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-dot" />
          <div>
            <div className="brand-name">ALBA data_IA</div>
            <div className="brand-sub">Demostrador · Reto IABiomed 2 · Valencia</div>
          </div>
        </div>
        <div className="header-right">
          <div className="tech-badge">
            <span className="badge-dot" />
            Groq llama3-8b · sub-100ms
          </div>
          <div className="tech-badge tech-badge--green">
            <span className="badge-dot badge-dot--green" />
            Salamandra-7B BSC
          </div>
          <div className="status-badge">
            <span className="live-dot" />
            Live
          </div>
        </div>
      </header>

      <div className="main">
        {/* Sidebar */}
        <aside className="sidebar">
          <section className="sidebar-section">
            <h3 className="section-label">Métricas de ahorro estimado</h3>
            {metrics ? (
              <MetricsPanel metrics={metrics} optimized={optimized} />
            ) : (
              <div className="skeleton" />
            )}
          </section>

          <section className="sidebar-section">
            <h3 className="section-label">Rutas en Valencia</h3>
            <RouteList
              activeRoute={activeRoute}
              onSelect={setActiveRoute}
              optimized={optimized}
            />
          </section>
        </aside>

        {/* Content area */}
        <div className="content">
          <nav className="tab-bar">
            {TABS.map((tab, i) => (
              <button
                key={tab}
                className={`tab ${i === activeTab ? "tab--active" : ""}`}
                onClick={() => setActiveTab(i)}
              >
                {tab}
              </button>
            ))}
          </nav>

          <div className="tab-content">
            {activeTab === 0 && (
              <MapPanel
                activeRoute={activeRoute}
                optimized={optimized}
              />
            )}
            {activeTab === 1 && <GisMapPanel />}
            {activeTab === 2 && (
              <MetricsPanel
                metrics={metrics}
                optimized={optimized}
                expanded
              />
            )}
          </div>

          <footer className="action-bar">
            <button
              className={`btn ${optimized ? "btn--success" : "btn--primary"}`}
              onClick={optimized ? handleReset : handleOptimize}
              disabled={loading}
            >
              {loading ? "⟳ Calculando rutas…" : optimized ? "↺ Resetear demo" : "▶ Optimizar rutas de reparto"}
            </button>

          </footer>

          <div className="impact-banner">
            🌱{" "}
            <strong>
              2.500 operadores × mismo ratio = retirar ~1.000 coches de Valencia al año.
            </strong>{" "}
            Factores CO₂: EU Reg. 2019/1242
          </div>
        </div>
      </div>
    </div>
  );
}
