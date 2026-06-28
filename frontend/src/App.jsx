/**
 * ECOFLUX — Frontend React
 * Demostrador del optimizador de rutas con React-Leaflet + métricas CO₂
 * Stack: React + Vite + React-Leaflet + Recharts + tRPC
 */

import React, { useState, useEffect } from "react";
import {
  Button,
  Chip,
  CssBaseline,
  Tab,
  Tabs,
  ThemeProvider,
  createTheme,
} from "@mui/material";
import MapPanel from "./components/MapPanel";
import MetricsPanel from "./components/MetricsPanel";
import RouteList from "./components/RouteList";
import GisMapPanel from "./components/GisMapPanel";
import { fetchDemoMetrics, optimizeRoutes } from "./api/alba";
import logoUrl from "../logo.jpeg";
import "./styles/app.css";

const TABS = ["Mapa urbano", "Mapa ICV", "Métricas CO₂"];

const theme = createTheme({
  palette: {
    mode: "dark",
    background: { default: "#000000", paper: "#1a1a1a" },
    primary: { main: "#024ad8", light: "#296ef9", dark: "#0e3191", contrastText: "#ffffff" },
    secondary: { main: "#8ebdce", contrastText: "#000000" },
    success: { main: "#32c86a", contrastText: "#001b0b" },
    warning: { main: "#ff5050", contrastText: "#ffffff" },
    text: { primary: "#ffffff", secondary: "#c2c2c2" },
    divider: "#3d3d3d",
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily: 'Inter, "Forma DJR Micro", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    button: { textTransform: "uppercase", fontWeight: 700, letterSpacing: 0.7 },
  },
});

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
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="app">
        <header className="topbar">
          <div className="brand">
            <img className="brand-logo" src={logoUrl} alt="ECOFLUX" />
            <div>
              <div className="brand-name">ECOFLUX</div>
              <div className="brand-sub">Demostrador · Reto IABiomed 2 · Valencia</div>
            </div>
          </div>
          <div className="header-right">
            <Chip className="tech-chip" label="Groq llama3-8b · sub-100ms" size="small" variant="outlined" />
            <Chip className="tech-chip tech-chip--green" label="Salamandra-7B BSC" size="small" variant="outlined" />
            <Chip className="live-chip" label="Live" size="small" color="success" />
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
            <Tabs
              value={activeTab}
              onChange={(_, tab) => setActiveTab(tab)}
              className="tab-bar"
              variant="scrollable"
              scrollButtons="auto"
            >
              {TABS.map((tab) => (
                <Tab key={tab} label={tab} />
              ))}
            </Tabs>

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
              <Button
                variant="contained"
                color={optimized ? "success" : "primary"}
                onClick={optimized ? handleReset : handleOptimize}
                disabled={loading}
              >
                {loading ? "Calculando rutas..." : optimized ? "Resetear demo" : "Optimizar rutas de reparto"}
              </Button>

            </footer>

            <div className="impact-banner">
              <strong>
                2.500 operadores x mismo ratio = retirar ~1.000 coches de Valencia al año.
              </strong>{" "}
              Factores CO₂: EU Reg. 2019/1242
            </div>
          </div>
        </div>
      </div>
    </ThemeProvider>
  );
}
