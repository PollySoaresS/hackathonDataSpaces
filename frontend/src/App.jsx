/**
 * ECOFLUX — Frontend React
 * Stepper demo para coordinación logística en la Comunitat Valenciana.
 */

import React, { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CssBaseline,
  FormControlLabel,
  Grid,
  MenuItem,
  Paper,
  Stack,
  Step,
  StepButton,
  Stepper,
  TextField,
  ThemeProvider,
  Typography,
  createTheme,
  useMediaQuery,
} from "@mui/material";
import MapPanel from "./components/MapPanel";
import {
  analyzeOverlap,
  createDelivery,
  createOperator,
  optimizeDynamicRoute,
} from "./api/alba";
import logoUrl from "../logo.jpeg";
import "./styles/app.css";

const STEPS = [
  ["Operador", "Autenticación y datos mínimos del operador"],
  ["Entrega", "Puntos de carga y descarga en la Comunitat Valenciana"],
  ["Privacidad", "Soberanía de datos y anonimización"],
  ["Solapamiento", "Detección de entregas compatibles entre operadores"],
  ["Mapa", "Selección dinámica de puntos y rutas optimizadas"],
];

const AREA_OPTIONS = ["Valencia centro", "Ciutat Vella", "Ruzafa", "Extramurs", "El Cabanyal", "Alicante", "Castellón", "Other"];
const ENTRY_MODES = [
  { value: "PRIVATE_COMPANY", label: "Empresa privada", hint: "Plan diario de rutas y flota corporativa" },
  { value: "INDIVIDUAL_PERSON", label: "Persona individual", hint: "Operador autónomo o reparto puntual" },
];
const VEHICLE_TYPES = ["Flota mixta", "Furgoneta diésel", "Furgoneta eléctrica", "Cargo bike", "Reparto a pie"];
const PRIORITIES = ["Baja", "Normal", "Alta"];
const RELOAD_OPTIONS = [
  { value: "manual", label: "Manual", ms: 0 },
  { value: "10s", label: "Cada 10 segundos", ms: 10000 },
  { value: "30s", label: "Cada 30 segundos", ms: 30000 },
  { value: "1m", label: "Cada 1 minuto", ms: 60000 },
  { value: "5m", label: "Cada 5 minutos", ms: 300000 },
];
const FILE_EXTENSIONS = ".json,.geojson,.xml,.gpx,.kml,.csv";
const TIME_OPTIONS = Array.from({ length: 39 }, (_, index) => {
  const minutes = 240 + index * 30;
  return `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
});
const COMPANY_PLAN = {
  clientName: "DHL",
  planDate: "28/06/2026",
  zone: "Valencia ciudad",
  totalRoutes: 156,
  plannedKm: 2547,
  zeroEmissionRoutesPercentage: 42,
  co2SavingWithOptimization: 31,
};

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

const initialOperator = {
  operatorType: "PRIVATE_COMPANY",
  name: COMPANY_PLAN.clientName,
  email: "",
  vehicleType: "Flota mixta",
  licensePlate: "",
  driverId: "",
};

const initialDelivery = {
  area: "Valencia centro",
  timeStart: "",
  timeEnd: "",
  packageVolume: "",
  packageWeight: "",
  priority: "Normal",
  useDynamicPoints: false,
  loadingPointPending: true,
  unloadingPointPending: true,
};

const id = () => (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`);

function distanceKm(points) {
  const rad = (deg) => (deg * Math.PI) / 180;
  return points.slice(1).reduce((sum, point, index) => {
    const prev = points[index];
    const dLat = rad(point.lat - prev.lat);
    const dLon = rad(point.lon - prev.lon);
    const a = Math.sin(dLat / 2) ** 2
      + Math.cos(rad(prev.lat)) * Math.cos(rad(point.lat)) * Math.sin(dLon / 2) ** 2;
    return sum + 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }, 0);
}

function nearestNeighbor(points) {
  if (points.length < 3) return points;
  const [start, ...rest] = points;
  const route = [start];
  const pool = [...rest];

  while (pool.length) {
    const last = route[route.length - 1];
    let nextIndex = 0;
    let best = Infinity;
    pool.forEach((point, index) => {
      const distance = distanceKm([last, point]);
      if (distance < best) {
        best = distance;
        nextIndex = index;
      }
    });
    route.push(pool.splice(nextIndex, 1)[0]);
  }

  return route;
}

function nearestFrom(start, points) {
  const route = [];
  const pool = [...points];
  let current = start;

  while (pool.length) {
    let nextIndex = 0;
    let best = Infinity;
    pool.forEach((point, index) => {
      const distance = distanceKm([current, point]);
      if (distance < best) {
        best = distance;
        nextIndex = index;
      }
    });
    current = pool.splice(nextIndex, 1)[0];
    route.push(current);
  }

  return route;
}

function emissionFactor(vehicleType) {
  if (vehicleType.includes("diésel")) return 0.154;
  if (vehicleType.includes("eléctrica") || vehicleType.includes("Cargo") || vehicleType.includes("pie")) return 0.015;
  return 0.046;
}

function isLaterTime(end, start) {
  return TIME_OPTIONS.indexOf(end) > TIME_OPTIONS.indexOf(start);
}

function normalizePoint(point, label) {
  return { id: point.id || id(), label, lat: Number(point.lat), lon: Number(point.lon) };
}

function normalizeBackendRoute(data) {
  const points = data?.optimizedRoute || data?.optimized_route || data?.route || data?.points;
  if (!Array.isArray(points)) return null;
  return points.map((point, index) => normalizePoint({
    lat: point.lat ?? point.latitude,
    lon: point.lon ?? point.lng ?? point.longitude,
  }, point.label || `P${index + 1}`)).filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lon));
}

export default function App() {
  const mobile = useMediaQuery("(max-width: 760px)");
  const [activeStep, setActiveStep] = useState(0);
  const [maxStepReached, setMaxStepReached] = useState(0);
  const [operator, setOperator] = useState(initialOperator);
  const [operatorResult, setOperatorResult] = useState(null);
  const [delivery, setDelivery] = useState(initialDelivery);
  const [deliveryResult, setDeliveryResult] = useState(null);
  const [privacyOk, setPrivacyOk] = useState(false);
  const [overlap, setOverlap] = useState(null);
  const [loadingPoint, setLoadingPoint] = useState(null);
  const [unloadingPoint, setUnloadingPoint] = useState(null);
  const [waypoints, setWaypoints] = useState([]);
  const [mapMode, setMapMode] = useState("none");
  const [routeResult, setRouteResult] = useState(null);
  const [profileNotice, setProfileNotice] = useState("");
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [reloadInterval, setReloadInterval] = useState("manual");
  const [lastUpdated, setLastUpdated] = useState(() => new Date());
  const [isReloading, setIsReloading] = useState(false);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  const reloadOption = useMemo(
    () => RELOAD_OPTIONS.find((option) => option.value === reloadInterval) || RELOAD_OPTIONS[0],
    [reloadInterval],
  );

  useEffect(() => {
    if (!reloadOption.ms) {
      setIsReloading(false);
      return undefined;
    }

    let timeoutId;
    const intervalId = window.setInterval(() => {
      setIsReloading(true);
      setLastUpdated(new Date());
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => setIsReloading(false), 650);
    }, reloadOption.ms);

    return () => {
      window.clearInterval(intervalId);
      window.clearTimeout(timeoutId);
    };
  }, [reloadOption.ms]);

  const operatorReady = operator.name.trim()
    && operator.operatorType
    && operator.vehicleType;
  const deliveryReady = delivery.area
    && delivery.timeStart
    && delivery.timeEnd
    && isLaterTime(delivery.timeEnd, delivery.timeStart)
    && Number(delivery.packageVolume) > 0
    && Number(delivery.packageWeight) > 0
    && delivery.priority;

  const selectedPoints = useMemo(() => (
    delivery.useDynamicPoints && (loadingPoint || unloadingPoint)
      ? [loadingPoint, ...waypoints, unloadingPoint].filter(Boolean)
      : delivery.useDynamicPoints ? waypoints : []
  ), [delivery.useDynamicPoints, loadingPoint, unloadingPoint, waypoints]);

  const updateOperator = (field) => (event) => setOperator({ ...operator, [field]: event.target.value });
  const selectEntryMode = (operatorType) => {
    setOperator({
      ...operator,
      operatorType,
      name: operatorType === "PRIVATE_COMPANY" ? COMPANY_PLAN.clientName : "",
      vehicleType: operatorType === "PRIVATE_COMPANY" ? "Flota mixta" : "Cargo bike",
    });
    setOperatorResult(null);
  };
  const updateDelivery = (field) => (event) => {
    const value = event.target.value;
    if (field === "useDynamicPoints" && !value) {
      setLoadingPoint(null);
      setUnloadingPoint(null);
      setWaypoints([]);
      setRouteResult(null);
      setMapMode("none");
    }
    setDelivery({ ...delivery, [field]: value });
  };

  async function saveOperator() {
    if (!operatorReady) {
      setMessage("Completa los datos obligatorios del operador.");
      return false;
    }
    setBusy("operator");
    setMessage("");
    const payload = {
      name: operator.name,
      clientName: operator.name,
      operatorType: operator.operatorType,
      vehicle_type: operator.vehicleType,
      companyRoutePlan: operator.operatorType === "PRIVATE_COMPANY" ? COMPANY_PLAN : null,
      ...(operator.email ? { email: operator.email } : {}),
      ...(operator.licensePlate ? { license_plate: operator.licensePlate } : {}),
      ...(operator.driverId ? { driver_id: operator.driverId } : {}),
    };

    try {
      const data = await createOperator(payload);
      setOperatorResult({ id: data.operatorId || data.operator_id || data.anonymizedOperatorId || data.id || `op-${id().slice(0, 8)}`, source: "backend" });
    } catch {
      setOperatorResult({ id: `op-demo-${id().slice(0, 8)}`, source: "demo local" });
    } finally {
      setOperator((current) => ({ ...current, licensePlate: "", driverId: "" }));
      setBusy("");
    }
    return true;
  }

  async function saveDelivery() {
    if (!deliveryReady) {
      setMessage(delivery.timeStart && delivery.timeEnd && !isLaterTime(delivery.timeEnd, delivery.timeStart)
        ? "La hora final debe ser posterior a la hora inicial."
        : "Completa los datos obligatorios de la entrega.");
      return false;
    }
    setBusy("delivery");
    setMessage("");
    const payload = {
      area: delivery.area,
      time_window: { start: delivery.timeStart, end: delivery.timeEnd },
      package: {
        volume: Number(delivery.packageVolume),
        weight: Number(delivery.packageWeight),
        priority: delivery.priority,
      },
      loading_point: null,
      unloading_point: null,
      wantsMapPointSelection: delivery.useDynamicPoints,
      loading_point_pending: delivery.useDynamicPoints,
      unloading_point_pending: delivery.useDynamicPoints,
    };

    try {
      const data = await createDelivery(payload);
      setDeliveryResult({ id: data.deliveryId || data.delivery_id || data.id || `del-${id().slice(0, 8)}`, source: "backend" });
    } catch {
      setDeliveryResult({ id: `del-demo-${id().slice(0, 8)}`, source: "demo local" });
    } finally {
      setBusy("");
    }
    return true;
  }

  async function detectOverlap() {
    setBusy("overlap");
    setMessage("");
    const payload = { operator: safeOperatorPayload(), delivery };
    try {
      const data = await analyzeOverlap(payload);
      setOverlap(normalizeOverlap(data));
    } catch {
      setOverlap({
        area: delivery.area,
        compatibleOperators: delivery.area.includes("Valencia") || delivery.area === "Ciutat Vella" ? 3 : 2,
        compatibleDeliveries: delivery.priority === "Alta" ? 4 : 3,
        timeWindowCompatibility: `${delivery.timeStart} - ${delivery.timeEnd}`,
        totalVolume: Number(delivery.packageVolume) * 3,
        totalWeight: Number(delivery.packageWeight) * 3,
        consolidationPossible: true,
        suggestedVehicle: operator.vehicleType.includes("eléctrica") ? "Furgoneta eléctrica" : "Cargo bike + microhub",
        estimatedBenefit: `Entregas compatibles en ${delivery.area}; la carga agregada cabe en una ruta consolidada.`,
        source: "demo local",
      });
    } finally {
      setBusy("");
    }
  }

  function safeOperatorPayload() {
    return {
      operator_id: operatorResult?.id,
      operatorType: operator.operatorType,
      vehicle_type: operator.vehicleType,
      companyRoutePlan: operator.operatorType === "PRIVATE_COMPANY" ? COMPANY_PLAN : null,
    };
  }

  function normalizeOverlap(data) {
    return {
      area: data.area || delivery.area,
      compatibleOperators: data.compatibleOperators || data.compatible_operators || 0,
      compatibleDeliveries: data.compatibleDeliveries || data.compatible_deliveries || 0,
      timeWindowCompatibility: data.timeWindowCompatibility || data.time_window_compatibility || `${delivery.timeStart} - ${delivery.timeEnd}`,
      totalVolume: data.totalVolume || data.total_volume || Number(delivery.packageVolume),
      totalWeight: data.totalWeight || data.total_weight || Number(delivery.packageWeight),
      consolidationPossible: Boolean(data.consolidationPossible ?? data.consolidation_possible ?? true),
      suggestedVehicle: data.suggestedVehicle || data.suggested_vehicle || operator.vehicleType,
      estimatedBenefit: data.estimatedBenefit || data.estimated_benefit || "Consolidación posible con datos de área.",
      source: "backend",
    };
  }

  function handleMapPoint(latlng) {
    if (!delivery.useDynamicPoints) return;
    const point = { id: id(), lat: Number(latlng.lat.toFixed(6)), lon: Number(latlng.lng.toFixed(6)) };
    setRouteResult(null);
    if (mapMode === "loading") {
      setLoadingPoint({ ...point, label: "Carga" });
      setDelivery({ ...delivery, loadingPointPending: false });
      setMapMode("none");
    } else if (mapMode === "unloading") {
      setUnloadingPoint({ ...point, label: "Descarga" });
      setDelivery({ ...delivery, unloadingPointPending: false });
      setMapMode("none");
    } else if (mapMode === "waypoint") {
      setWaypoints([...waypoints, { ...point, label: `W${waypoints.length + 1}` }]);
    }
  }

  function removePoint(kind, pointId) {
    setRouteResult(null);
    if (kind === "loading") {
      setLoadingPoint(null);
      setDelivery({ ...delivery, loadingPointPending: true });
    } else if (kind === "unloading") {
      setUnloadingPoint(null);
      setDelivery({ ...delivery, unloadingPointPending: true });
    } else {
      setWaypoints(waypoints.filter((point) => point.id !== pointId).map((point, index) => ({ ...point, label: `W${index + 1}` })));
    }
  }

  function clearPoints() {
    setLoadingPoint(null);
    setUnloadingPoint(null);
    setWaypoints([]);
    setRouteResult(null);
    setMapMode("none");
    setDelivery({ ...delivery, loadingPointPending: true, unloadingPointPending: true });
  }

  async function optimizeRoute() {
    setMessage("");
    if (!((loadingPoint && unloadingPoint) || waypoints.length >= 2)) {
      setMessage(delivery.useDynamicPoints
        ? "Selecciona punto de carga y descarga, o al menos dos waypoints."
        : "Esta entrega está guardada solo a nivel de área. Activa la selección de puntos en Entrega para optimizar en mapa.");
      return;
    }
    setBusy("route");
    const original = selectedPoints;
    const fallbackOptimized = loadingPoint && unloadingPoint
      ? [loadingPoint, ...nearestFrom(loadingPoint, waypoints), unloadingPoint]
      : nearestNeighbor(waypoints);
    let optimizedPoints = fallbackOptimized;
    let source = "demo local";

    try {
      const data = await optimizeDynamicRoute({
        operatorId: operatorResult?.id,
        vehicleType: operator.vehicleType,
        delivery,
        loadingPoint,
        unloadingPoint,
        dynamicWaypoints: waypoints,
      });
      optimizedPoints = normalizeBackendRoute(data) || fallbackOptimized;
      source = "backend";
    } catch {
      // Backend opcional para demo hackathon.
    } finally {
      setBusy("");
    }

    const originalDistance = distanceKm(original);
    const optimizedDistance = distanceKm(optimizedPoints);
    const factor = emissionFactor(operator.vehicleType);
    setRouteResult({
      source,
      originalRoute: original,
      optimizedRoute: optimizedPoints,
      metrics: {
        vehicles: optimizedPoints.length > 3 ? 2 : 1,
        distance: `${originalDistance.toFixed(1)} km → ${optimizedDistance.toFixed(1)} km`,
        co2: `${(originalDistance * factor).toFixed(2)} kg → ${(optimizedDistance * factor).toFixed(2)} kg`,
        saving: `${Math.max(0, Math.round((1 - optimizedDistance / Math.max(originalDistance, 0.1)) * 100))}% estimado`,
      },
    });
  }

  async function goNext() {
    if (activeStep === 0 && !(await saveOperator())) return;
    if (activeStep === 1 && !(await saveDelivery())) return;
    if (activeStep === 2 && !privacyOk) {
      setMessage("Confirma la privacidad para continuar.");
      return;
    }
    if (activeStep === 3 && !overlap) {
      setMessage("Detecta el solapamiento antes de continuar.");
      return;
    }
    setMessage("");
    const nextStep = Math.min(activeStep + 1, STEPS.length - 1);
    setMaxStepReached(Math.max(maxStepReached, nextStep));
    setActiveStep(nextStep);
  }

  const primaryLabel = ["Crear operador", "Guardar entrega", "Confirmar privacidad", "Siguiente", "Finalizar selección"][activeStep];

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="app">
        <header className="topbar">
          <div className="brand">
            <img className="brand-logo" src={logoUrl} alt="ECOFLUX" />
            <div>
              <div className="brand-name">ECOFLUX</div>
              <div className="brand-sub">CargaSync Valencia · Data Space logístico</div>
            </div>
          </div>
          <div className="header-right">
            <Chip className="tech-chip" label="Valencia / Comunitat Valenciana" size="small" variant="outlined" />
            <Chip className="tech-chip tech-chip--green" label="Demo con fallback local" size="small" variant="outlined" />
            <Button
              className="profile-button"
              size="small"
              variant="outlined"
              onClick={() => {
                setProfileNotice("Ajustes de perfil no disponibles en la demo");
                window.setTimeout(() => setProfileNotice(""), 2400);
              }}
            >
              Perfil
            </Button>
          </div>
        </header>
        {profileNotice ? <Alert className="profile-notice" severity="info">{profileNotice}</Alert> : null}

        <main className="flow-shell">
          <Stepper activeStep={activeStep} orientation={mobile ? "vertical" : "horizontal"} className="flow-stepper">
            {STEPS.map(([label, subtitle], index) => (
              <Step key={label} completed={index < maxStepReached}>
                <StepButton
                  disabled={index > maxStepReached}
                  onClick={() => setActiveStep(index)}
                  optional={!mobile ? null : <Typography variant="caption">{subtitle}</Typography>}
                >
                  {label}
                </StepButton>
              </Step>
            ))}
          </Stepper>

          <Paper className="flow-card" elevation={0}>
            <Stack spacing={2}>
              <Box>
                <Typography variant="overline" color="text.secondary">{STEPS[activeStep][0]}</Typography>
                <Typography variant="h5">{STEPS[activeStep][1]}</Typography>
              </Box>

              {message ? <Alert severity="warning">{message}</Alert> : null}

              {activeStep === 0 ? (
                <OperatorStep
                  operator={operator}
                  update={updateOperator}
                  selectEntryMode={selectEntryMode}
                  operatorResult={operatorResult}
                />
              ) : null}
              {activeStep === 1 ? (
                <DeliveryStep
                  delivery={delivery}
                  update={updateDelivery}
                  deliveryResult={deliveryResult}
                  uploadedFileName={uploadedFileName}
                  setUploadedFileName={setUploadedFileName}
                  reloadInterval={reloadInterval}
                  setReloadInterval={setReloadInterval}
                />
              ) : null}
              {activeStep === 2 ? (
                <PrivacyStep privacyOk={privacyOk} setPrivacyOk={setPrivacyOk} />
              ) : null}
              {activeStep === 3 ? (
                <OverlapStep overlap={overlap} busy={busy} detectOverlap={detectOverlap} />
              ) : null}
              {activeStep === 4 ? (
                <MapStep
                  mapMode={mapMode}
                  setMapMode={setMapMode}
                  loadingPoint={loadingPoint}
                  unloadingPoint={unloadingPoint}
                  waypoints={waypoints}
                  onMapPoint={handleMapPoint}
                  removePoint={removePoint}
                  clearPoints={clearPoints}
                  optimizeRoute={optimizeRoute}
                  busy={busy}
                  routeResult={routeResult}
                  companyPlan={COMPANY_PLAN}
                  canSelectPoints={delivery.useDynamicPoints}
                  reloadInterval={reloadInterval}
                  setReloadInterval={setReloadInterval}
                  reloadOption={reloadOption}
                  lastUpdated={lastUpdated}
                  isReloading={isReloading}
                />
              ) : null}
            </Stack>
          </Paper>

          <footer className="flow-actions">
            <Button disabled={activeStep === 0 || Boolean(busy)} onClick={() => setActiveStep(activeStep - 1)}>
              Atrás
            </Button>
            {activeStep < 4 ? (
              <Button
                variant="contained"
                onClick={goNext}
                disabled={Boolean(busy) || (activeStep === 2 && !privacyOk) || (activeStep === 3 && !overlap)}
              >
                {busy ? "Procesando..." : primaryLabel}
              </Button>
            ) : null}
          </footer>
        </main>
      </div>
    </ThemeProvider>
  );
}

function OperatorStep({ operator, update, selectEntryMode, operatorResult }) {
  return (
    <Stack spacing={2}>
      <div className="choice-grid">
        {ENTRY_MODES.map((mode) => (
          <Button
            key={mode.value}
            className={`onboarding-choice ${operator.operatorType === mode.value ? "onboarding-choice--active" : ""}`}
            variant={operator.operatorType === mode.value ? "contained" : "outlined"}
            onClick={() => selectEntryMode(mode.value)}
          >
            <strong>{mode.label}</strong>
            <span>{mode.hint}</span>
          </Button>
        ))}
      </div>
      {operator.operatorType === "PRIVATE_COMPANY" ? (
        <>
          <div className="company-header">
            <span>Nombre cliente: {COMPANY_PLAN.clientName}</span>
            <span>Plan rutas día: {COMPANY_PLAN.planDate}</span>
          </div>
          <div className="stat-grid">
            <Metric label="Zona" value={COMPANY_PLAN.zone} />
            <Metric label="Nº total de rutas" value={COMPANY_PLAN.totalRoutes} />
            <Metric label="Km de recorrido previstos" value={COMPANY_PLAN.plannedKm.toLocaleString("es-ES")} />
            <Metric label="% rutas 0 emisiones" value={`${COMPANY_PLAN.zeroEmissionRoutesPercentage}%`} />
            <Metric label="Ahorro CO₂ optimizado" value={`${COMPANY_PLAN.co2SavingWithOptimization}%`} />
          </div>
        </>
      ) : null}
      <Grid container spacing={2}>
      <Grid item xs={12} md={6}><TextField fullWidth required label="Nombre cliente / operador" value={operator.name} onChange={update("name")} /></Grid>
      <Grid item xs={12} md={6}><TextField fullWidth label="Email opcional" type="email" value={operator.email} onChange={update("email")} /></Grid>
      <Grid item xs={12} md={6}><SelectField label="Tipo de operador" value={operator.operatorType} onChange={(event) => selectEntryMode(event.target.value)} options={ENTRY_MODES.map((mode) => ({ label: mode.label, value: mode.value }))} /></Grid>
      <Grid item xs={12} md={6}><SelectField label="Tipo de flota / vehículo principal" value={operator.vehicleType} onChange={update("vehicleType")} options={VEHICLE_TYPES} /></Grid>
      <Grid item xs={12} md={6}><TextField fullWidth label="Matrícula opcional" value={operator.licensePlate} onChange={update("licensePlate")} /></Grid>
      <Grid item xs={12} md={6}><TextField fullWidth label="ID conductor opcional" value={operator.driverId} onChange={update("driverId")} /></Grid>
      {operatorResult ? (
        <Grid item xs={12}><Alert severity="success">Operador registrado como {operatorResult.id}. Los campos sensibles no se muestran de nuevo.</Alert></Grid>
      ) : null}
      </Grid>
    </Stack>
  );
}

function DeliveryStep({
  delivery,
  update,
  deliveryResult,
  uploadedFileName,
  setUploadedFileName,
  reloadInterval,
  setReloadInterval,
}) {
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}><SelectField label="Área de entrega" value={delivery.area} onChange={update("area")} options={AREA_OPTIONS} /></Grid>
      <Grid item xs={6} md={3}><SelectField label="Inicio ventana" value={delivery.timeStart} onChange={update("timeStart")} options={TIME_OPTIONS} /></Grid>
      <Grid item xs={6} md={3}><SelectField label="Fin ventana" value={delivery.timeEnd} onChange={update("timeEnd")} options={TIME_OPTIONS} /></Grid>
      {delivery.timeStart && delivery.timeEnd && !isLaterTime(delivery.timeEnd, delivery.timeStart) ? (
        <Grid item xs={12}><Alert severity="warning">La hora final debe ser posterior a la hora inicial.</Alert></Grid>
      ) : null}
      <Grid item xs={12} md={4}><TextField fullWidth required label="Volumen paquete" type="number" value={delivery.packageVolume} onChange={update("packageVolume")} inputProps={{ min: 0 }} /></Grid>
      <Grid item xs={12} md={4}><TextField fullWidth required label="Peso paquete" type="number" value={delivery.packageWeight} onChange={update("packageWeight")} inputProps={{ min: 0 }} /></Grid>
      <Grid item xs={12} md={4}><SelectField label="Prioridad" value={delivery.priority} onChange={update("priority")} options={PRIORITIES} /></Grid>
      <Grid item xs={12}>
        <FormControlLabel
          control={<Checkbox checked={delivery.useDynamicPoints} onChange={(event) => update("useDynamicPoints")({ target: { value: event.target.checked } })} />}
          label="Quiero seleccionar los puntos de carga y descarga en el mapa"
        />
      </Grid>
      {!delivery.useDynamicPoints ? (
        <Grid item xs={12}>
          <div className="upload-card">
            <Button variant="outlined" component="label">
              Cargar archivo de rutas
              <input
                hidden
                type="file"
                accept={FILE_EXTENSIONS}
                onChange={(event) => setUploadedFileName(event.target.files?.[0]?.name || "")}
              />
            </Button>
            <div>
              <strong>{uploadedFileName || "json, geojson, xml, gpx, kml, csv"}</strong>
              <p>Puedes cargar un archivo de rutas o puntos existente. En esta demo se guarda como referencia visual.</p>
            </div>
          </div>
        </Grid>
      ) : (
        <Grid item xs={12}><Alert severity="info">Los puntos exactos de carga y descarga se seleccionarán dinámicamente en el mapa del paso final.</Alert></Grid>
      )}
      <Grid item xs={12} md={6}>
        <SelectField
          label="Frecuencia de recarga"
          value={reloadInterval}
          onChange={(event) => setReloadInterval(event.target.value)}
          options={RELOAD_OPTIONS}
        />
      </Grid>
      {deliveryResult ? <Grid item xs={12}><Alert severity="success">Entrega guardada como solicitud de área: {deliveryResult.id}.</Alert></Grid> : null}
    </Grid>
  );
}

function PrivacyStep({ privacyOk, setPrivacyOk }) {
  const shared = ["Área de entrega", "Ventana horaria", "Volumen del paquete", "Peso del paquete", "Tipo de vehículo", "Capacidad del vehículo", "Clase de emisiones"];
  const protectedData = ["Identidad del cliente", "Dirección privada exacta", "Identidad del conductor", "Matrícula", "Estrategia comercial interna", "Identificadores brutos del operador"];
  return (
    <Stack spacing={2}>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}><DataList title="Compartido con el Data Space" items={shared} /></Grid>
        <Grid item xs={12} md={6}><DataList title="Protegido" items={protectedData} /></Grid>
      </Grid>
      <Alert severity="info">Solo se comparte el mínimo dato operativo necesario para coordinar. Los campos sensibles se anonimizan antes de entrar al Data Space.</Alert>
      <FormControlLabel
        control={<Checkbox checked={privacyOk} onChange={(event) => setPrivacyOk(event.target.checked)} />}
        label="Entiendo que solo se compartirán datos operativos mínimos para la coordinación."
      />
    </Stack>
  );
}

function OverlapStep({ overlap, busy, detectOverlap }) {
  return (
    <Stack spacing={2}>
      <Button variant="contained" onClick={detectOverlap} disabled={busy === "overlap"}>
        {busy === "overlap" ? "Analizando..." : "Detectar solapamiento"}
      </Button>
      {overlap ? (
        <div className="analysis-card">
          <Metric label="Área" value={overlap.area} />
          <Metric label="Operadores compatibles" value={overlap.compatibleOperators} />
          <Metric label="Entregas compatibles" value={overlap.compatibleDeliveries} />
          <Metric label="Ventana compatible" value={overlap.timeWindowCompatibility} />
          <Metric label="Volumen total" value={overlap.totalVolume} />
          <Metric label="Peso total" value={overlap.totalWeight} />
          <Metric label="Consolidación posible" value={overlap.consolidationPossible ? "Sí" : "No"} />
          <Metric label="Vehículo sugerido" value={overlap.suggestedVehicle} />
          <Alert severity="success">{overlap.estimatedBenefit}</Alert>
        </div>
      ) : (
        <Alert severity="info">El análisis funciona con entregas por área, sin exigir coordenadas exactas.</Alert>
      )}
    </Stack>
  );
}

function MapStep(props) {
  const {
    mapMode,
    setMapMode,
    loadingPoint,
    unloadingPoint,
    waypoints,
    onMapPoint,
    removePoint,
    clearPoints,
    optimizeRoute,
    busy,
    routeResult,
    companyPlan,
    canSelectPoints,
    reloadInterval,
    setReloadInterval,
    reloadOption,
    lastUpdated,
    isReloading,
  } = props;
  const selectedPoints = canSelectPoints ? [loadingPoint, ...waypoints, unloadingPoint].filter(Boolean) : [];

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} lg={8}>
        <Stack spacing={1.5}>
          <div className="map-plan-summary">
            <Metric label="Nombre cliente" value={companyPlan.clientName} />
            <Metric label="Plan rutas día" value={companyPlan.planDate} />
            <Metric label="Zona" value={companyPlan.zone} />
            <Metric label="Nº total de rutas" value={companyPlan.totalRoutes} />
            <Metric label="Km previstos" value={companyPlan.plannedKm.toLocaleString("es-ES")} />
            <Metric label="% 0 rutas vehiculos emisiones" value={`${companyPlan.zeroEmissionRoutesPercentage}%`} />
            <Metric label="Ahorro CO₂ optimizado" value={`${companyPlan.co2SavingWithOptimization}%`} />
          </div>
          <div className="map-mode-bar">
            <Button disabled={!canSelectPoints} variant={mapMode === "loading" ? "contained" : "outlined"} onClick={() => setMapMode("loading")}>Seleccionar punto de carga</Button>
            <Button disabled={!canSelectPoints} variant={mapMode === "unloading" ? "contained" : "outlined"} onClick={() => setMapMode("unloading")}>Seleccionar punto de descarga</Button>
            <Button disabled={!canSelectPoints} variant={mapMode === "waypoint" ? "contained" : "outlined"} onClick={() => setMapMode("waypoint")}>Añadir waypoint</Button>
            <Button disabled={!canSelectPoints} variant="outlined" onClick={() => setMapMode("none")}>Finalizar selección</Button>
            <Button disabled={!canSelectPoints} color="warning" variant="outlined" onClick={clearPoints}>Limpiar puntos</Button>
            <Button variant="contained" onClick={optimizeRoute} disabled={busy === "route"}>
              {busy === "route" ? "Optimizando..." : "Optimizar rutas"}
            </Button>
            <TextField
              select
              size="small"
              label="Frecuencia de recarga"
              value={reloadInterval}
              onChange={(event) => setReloadInterval(event.target.value)}
              className="map-refresh-select"
            >
              {RELOAD_OPTIONS.map((option) => <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>)}
            </TextField>
          </div>
          <Alert severity={!canSelectPoints ? "info" : mapMode === "none" ? "info" : "success"}>
            {!canSelectPoints
              ? "Entrega guardada solo a nivel de área. Vuelve a Entrega si quieres seleccionar puntos exactos."
              : mapMode === "none" ? "El mapa no crea puntos hasta activar un modo de selección." : "Haz clic en el mapa para crear el punto dinámico."}
          </Alert>
          <MapPanel
            mapMode={mapMode}
            loadingPoint={loadingPoint}
            unloadingPoint={unloadingPoint}
            waypoints={waypoints}
            originalRoute={routeResult?.originalRoute || selectedPoints}
            optimizedRoute={routeResult?.optimizedRoute || []}
            onMapPoint={onMapPoint}
            canSelectPoints={canSelectPoints}
            reloadLabel={reloadOption.label}
            lastUpdated={lastUpdated}
            isReloading={isReloading}
          />
        </Stack>
      </Grid>
      <Grid item xs={12} lg={4}>
        <Stack spacing={2}>
          <PointSummary
            loadingPoint={loadingPoint}
            unloadingPoint={unloadingPoint}
            waypoints={waypoints}
            removePoint={removePoint}
          />
          <TechnicalCoordinates loadingPoint={loadingPoint} unloadingPoint={unloadingPoint} waypoints={waypoints} />
          {routeResult ? <RouteMetrics routeResult={routeResult} /> : null}
        </Stack>
      </Grid>
    </Grid>
  );
}

function PointSummary({ loadingPoint, unloadingPoint, waypoints, removePoint }) {
  const hasPoints = Boolean(loadingPoint || unloadingPoint || waypoints.length);
  return (
    <div className="point-summary">
      <Typography variant="subtitle2">Resumen de puntos</Typography>
      {!hasPoints ? <p>No hay puntos seleccionados todavía.</p> : null}
      <div className="point-summary-list">
        <PointCard label="Carga" point={loadingPoint} onRemove={() => removePoint("loading")} />
        <PointCard label="Descarga" point={unloadingPoint} onRemove={() => removePoint("unloading")} />
        {waypoints.map((point) => (
          <PointCard key={point.id} label={point.label} point={point} onRemove={() => removePoint("waypoint", point.id)} />
        ))}
      </div>
    </div>
  );
}

function PointCard({ label, point, onRemove }) {
  return (
    <div className={`point-card ${point ? "" : "point-card--pending"}`}>
      <strong>{label}</strong>
      <span>{point ? "Seleccionado" : "Pendiente"}</span>
      {point ? <button type="button" className="point-remove" onClick={onRemove} aria-label={`Quitar ${label}`}>x</button> : null}
    </div>
  );
}

function TechnicalCoordinates({ loadingPoint, unloadingPoint, waypoints }) {
  const items = [
    loadingPoint ? `Carga: ${loadingPoint.lat}, ${loadingPoint.lon}` : null,
    unloadingPoint ? `Descarga: ${unloadingPoint.lat}, ${unloadingPoint.lon}` : null,
    ...waypoints.map((point) => `${point.label}: ${point.lat}, ${point.lon}`),
  ].filter(Boolean);

  return (
    <details className="technical-details">
      <summary>Ver coordenadas técnicas</summary>
      {items.length ? (
        <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>
      ) : (
        <p>Sin coordenadas seleccionadas.</p>
      )}
    </details>
  );
}

function RouteMetrics({ routeResult }) {
  return (
    <div className="metrics-summary">
      <Metric label="Origen" value={routeResult.source} />
      <Metric label="Vehículos" value={routeResult.metrics.vehicles} />
      <Metric label="Distancia" value={routeResult.metrics.distance} />
      <Metric label="CO₂" value={routeResult.metrics.co2} />
      <Metric label="Ahorro" value={routeResult.metrics.saving} />
    </div>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <TextField select fullWidth required label={label} value={value} onChange={onChange}>
      {options.map((option) => {
        const item = typeof option === "string" ? { label: option, value: option } : option;
        return <MenuItem key={item.value} value={item.value}>{item.label}</MenuItem>;
      })}
    </TextField>
  );
}

function DataList({ title, items }) {
  return (
    <div className="data-list">
      <Typography variant="subtitle2">{title}</Typography>
      <ul>
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric-row">
      <span>{label}</span>
      <strong>{String(value)}</strong>
    </div>
  );
}
