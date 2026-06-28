# ECOFLUX — ALBA data_IA

**Plataforma territorial inteligente para la Comunitat Valenciana**  
Optimización de rutas urbanas · Anonimización PHI · Análisis de riesgo climático · Pipeline IA ensemble anti-alucinación  
Reto IABiomed 2 · Valencia · 2026

---

## Guía para el equipo de frontend — Ampliaciones pendientes

> Elaborada por el arquitecto de sistema. Lee esta sección **antes de tocar código**.  
> Stack actual: React 18 + Vite + MUI v5 + Leaflet + Recharts. Backend: FastAPI en `localhost:8001`.

### Estado actual verificado ✅

| Módulo | Estado | Endpoint backend |
|---|---|---|
| Mapa Leaflet con rutas Valencia | ✅ Funciona | — (datos hardcoded en `MapPanel.jsx`) |
| Mapa ICV (WMS/WFS) | ✅ Funciona | `GET /api/gis/layers` |
| Métricas CO₂ básicas | ✅ Funciona | `GET /api/optimize/demo` |
| Optimización Clarke-Wright | ✅ Funciona | `POST /api/optimize/` |
| Anonimización PHI | ✅ Funciona | `POST /api/anonymize/` |
| Pipeline IA ensemble 3 capas | ✅ Backend listo | respuesta en `summary` del optimize |

---

### Ampliación 1 — Panel de análisis IA (PRIORIDAD ALTA)

**Qué falta:** el backend ya devuelve `summary` con el análisis del ensemble IA tras cada optimización. El frontend no lo muestra.

**Dónde tocar:** `src/App.jsx` → guardar en state y pasar al sidebar. Crear `src/components/IAPanel.jsx`.

**Contrato de datos** (lo que devuelve `POST /api/optimize/`):
```json
{
  "routes": [...],
  "distance_before_km": 103,
  "distance_after_km": 66,
  "co2_savings_kg": 11.7,
  "summary": "La ruta tiene una eficiencia alta con 5.2 km y 0 kg CO₂.",
  "confidence": 0.95,
  "hallucination": false
}
```

**Código de partida para `IAPanel.jsx`:**
```jsx
// src/components/IAPanel.jsx
export default function IAPanel({ summary, confidence, hallucination }) {
  if (!summary) return null;
  const color = hallucination ? "#ff5050" : confidence > 0.8 ? "#32c86a" : "#eda100";
  return (
    <section style={{ padding: "12px", border: `1px solid ${color}`, borderRadius: 8, marginTop: 16 }}>
      <p style={{ fontSize: 13, color: "#c2c2c2" }}>{summary}</p>
      <span style={{ fontSize: 11, color }}>
        Confianza: {(confidence * 100).toFixed(0)}%
        {hallucination && " ⚠️ revisar"}
      </span>
    </section>
  );
}
```

**Integración en App.jsx:**
```jsx
// Añadir al state:
const [iaResult, setIaResult] = useState(null);

// En handleOptimize():
const result = await optimizeRoutes(true);
setIaResult(result); // { summary, confidence, hallucination }
setOptimized(true);

// En el JSX sidebar:
<IAPanel {...iaResult} />
```

---

### Ampliación 2 — Métricas CO₂ con gráfica Recharts (PRIORIDAD ALTA)

**Qué falta:** `MetricsPanel.jsx` solo muestra texto plano. Recharts ya está instalado.

**Contrato:** `GET /api/metrics/impact?operators=2500` devuelve:
```json
{
  "operators": 2500,
  "co2_saved_per_day_kg": 29250,
  "co2_saved_per_year_t": 10676,
  "equivalent_cars_removed": 1069
}
```

**Patrón a seguir en MetricsPanel.jsx:**
```jsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const chartData = [
  { name: "Antes", co2: metrics.co2_before_kg, fill: "#ff5050" },
  { name: "Después", co2: metrics.co2_after_kg, fill: "#32c86a" },
];

<ResponsiveContainer width="100%" height={160}>
  <BarChart data={chartData}>
    <XAxis dataKey="name" tick={{ fill: "#c2c2c2", fontSize: 11 }} />
    <YAxis tick={{ fill: "#c2c2c2", fontSize: 11 }} unit=" kg" />
    <Tooltip formatter={(v) => `${v} kg CO₂`} />
    <Bar dataKey="co2" radius={[4, 4, 0, 0]}>
      {chartData.map((e, i) => <Cell key={i} fill={e.fill} />)}
    </Bar>
  </BarChart>
</ResponsiveContainer>
```

---

### Ampliación 3 — Entrada de rutas personalizadas por el usuario

**Qué falta:** permitir al usuario pegar coordenadas o seleccionar paradas en el mapa y optimizarlas.

**Contrato `POST /api/optimize/`** con paradas reales:
```json
{
  "stops": [
    { "id": "1", "lat": 39.473, "lon": -0.378, "demand": 1 },
    { "id": "2", "lat": 39.465, "lon": -0.366, "demand": 1 }
  ],
  "use_demo": false
}
```

**Patrón recomendado:** campo `textarea` en sidebar + `JSON.parse()` + llamar `optimizeRoutes(stops)`.  
**Importante:** añadir en `api/alba.js`:
```js
export const optimizeRoutes = (useDemoOrStops) => {
  const body = typeof useDemoOrStops === "boolean"
    ? { use_demo: useDemoOrStops }
    : { stops: useDemoOrStops, use_demo: false };
  return apiFetch("/api/optimize/", { method: "POST", body: JSON.stringify(body) });
};
```

---

### Ampliación 4 — Anonimizador de texto (panel ya existe, falta conectarlo)

**Componente:** `AnonymizerPanel.jsx` ya está creado.  
**Falta:** importarlo en `App.jsx` y añadirlo como cuarta tab.

```jsx
// App.jsx — añadir tab:
const TABS = ["Mapa urbano", "Mapa ICV", "Métricas CO₂", "Anonimizador PHI"];

// En el render de tabs:
{activeTab === 3 && <AnonymizerPanel />}
```

**Endpoint:** `POST /api/anonymize/` — ver `src/api/alba.js` → `anonymizeText()`.

---

### Reglas de arquitectura — NO violar

1. **Nunca hardcodear la URL del backend.** Siempre usar `VITE_API_URL` via `src/api/alba.js`.
2. **El estado global vive en `App.jsx`.** Los componentes son puros (reciben props, no hacen fetch propios excepto `GisMapPanel`).
3. **El tema MUI es la única fuente de colores.** No usar colores inline ad-hoc; usar `theme.palette.success.main`, etc.
4. **Leaflet y MUI tienen conflicto de z-index.** Los overlays sobre el mapa necesitan `zIndex: 9999` explícito.
5. **CORS ya configurado** para `localhost:5173` y `localhost:5175`. Si cambias el puerto, actualiza `ALLOWED_ORIGINS` en `docker-compose.yml`.
6. **No instalar nuevas dependencias** sin confirmar con el arquitecto. El `package-lock.json` se rompe fácil en Docker.

---

### Flujo de desarrollo local

```bash
# 1. Arrancar todo (primera vez o tras pull)
docker compose up --build -d

# 2. Ver logs del frontend en tiempo real
docker logs -f alba-frontend

# 3. Si instalas un paquete nuevo, rebuild obligatorio
docker compose restart frontend
# O si cambió package.json:
docker compose up --build -d frontend

# 4. Backend docs interactivos
http://localhost:8001/api/docs

# 5. Health check
curl http://localhost:8001/api/health
```

---

### Variables de entorno necesarias (`backend/.env`)

```env
GROQ_API_KEY=gsk_...        # Pipeline IA ensemble (obligatorio)
HMAC_SECRET=...             # Mínimo 32 chars (obligatorio)
HF_API_KEY=hf_...           # HuggingFace Salamandra (opcional, fallback)
DEEPSEEK_API_KEY=sk-...     # DeepSeek (opcional, fallback)
AEMET_API_KEY=...           # Datos meteorológicos CV (opcional, Fase 2)
```

---

---

## Inicio rápido

```bash
# Backend — funciona offline con fallbacks
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000/api/docs

# Frontend — React + Vite
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Arquitectura general

```
FRONTEND  React 18 + Vite 8.1
  Leaflet (MapPanel) · OpenLayers 10.9 (GisMapPanel)
  Recharts (MetricsPanel) · SpeechRecognition API (AnonymizerPanel)
          │ HTTP REST JSON
BACKEND  FastAPI + Uvicorn · Python 3.13 · Arquitectura Hexagonal
  /api/optimize      → OptimizeUseCase    → RouteService (Clarke-Wright VRP)
  /api/anonymize     → AnonymizeUseCase   → AI pipeline: Groq+Salamandra+DeepSeek+HMAC
  /api/metrics       → métricas CO₂ EU Reg. 2019/1242
  /api/gis           → GisUseCase         → IcvGisAdapter (WMS/WFS/WMTS)
  /api/territorial   → TerritorialUseCase → IcvTerritorialAdapter [Fase 1]
  /api/weather       → WeatherUseCase     → AemetAdapter          [Fase 2]
  /api/climate       → ClimateUseCase     → CopernicusAdapter     [Fase 3]
  /api/risk          → RiskUseCase        → RiskService DS4M      [Fase 4]
          │
SERVICIOS EXTERNOS
  ICV WFS/WMS  http://terramapas.icv.gva.es/0105_Delimitaciones (público, sin auth)
  AEMET        https://opendata.aemet.es/opendata/api            (gratuito con registro)
  Groq         https://api.groq.com  llama3-8b-8192              (plan gratuito 14.400 req/día)
  HuggingFace  BSC-LT/salamandra-7b-instruct                     (token gratuito)
  DeepSeek     https://api.deepseek.com/v1                       (fallback, opcional)
```

---

## Estructura de ficheros

```
alba_data_ia/
├── backend/
│   ├── main.py                              # FastAPI, CORS, 8 routers
│   ├── requirements.txt
│   ├── .env                                 # Secrets locales (no en git)
│   ├── .env.example                         # Plantilla completa
│   ├── Dockerfile / .dockerignore
│   ├── core/config.py                       # Pydantic Settings + validadores
│   ├── routes/                              # Adaptadores HTTP entrada (IN)
│   │   ├── optimize.py · anonymize.py · metrics.py · gis.py
│   │   ├── territorial.py   [Fase 1]
│   │   ├── weather.py       [Fase 2]
│   │   ├── climate.py       [Fase 3]
│   │   └── risk.py          [Fase 4]
│   ├── app/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   ├── anonymization_result.py
│   │   │   │   ├── territorial_context.py  [Fase 1]
│   │   │   │   ├── weather_risk.py         [Fase 2]
│   │   │   │   ├── climate_risk.py         [Fase 3]
│   │   │   │   └── risk_score.py           [Fase 4]
│   │   │   └── ports/
│   │   │       ├── gis_port.py · anonymization_port.py · route_optimizer_port.py
│   │   │       ├── territorial_port.py     [Fase 1]
│   │   │       ├── weather_port.py         [Fase 2]
│   │   │       ├── climate_port.py         [Fase 3]
│   │   │       └── risk_port.py            [Fase 4]
│   │   ├── infrastructure/adapters/
│   │   │   ├── icv_gis_adapter.py
│   │   │   ├── icv_territorial_adapter.py  [Fase 1] WFS municipios+comarcas+zonas ENP
│   │   │   ├── aemet_adapter.py            [Fase 2] OpenData + riesgo determinista
│   │   │   ├── copernicus_adapter.py       [Fase 3] IDW ERA5+EFFIS+PATRICOVA
│   │   │   ├── route_optimizer_adapter.py
│   │   │   └── anonymization_adapter.py
│   │   ├── services/
│   │   │   ├── route_service.py · anonymization_service.py · gis_service.py
│   │   │   ├── territorial_service.py [Fase 1]
│   │   │   ├── weather_service.py     [Fase 2]
│   │   │   ├── climate_service.py     [Fase 3]
│   │   │   └── risk_service.py        [Fase 4] DS4M motor central
│   │   └── use_cases/
│   │       ├── optimize_use_case.py   # climate_risk_weight param [Fase 5]
│   │       ├── territorial_use_case.py [Fase 1]
│   │       ├── weather_use_case.py    [Fase 2]
│   │       ├── climate_use_case.py    [Fase 3]
│   │       └── risk_use_case.py       [Fase 4] orquesta Climate+Weather→DS4M
│   ├── services/
│   │   ├── vrp_optimizer.py           # Clarke-Wright + Stop.climate_risk [Fase 5]
│   │   └── anonymizer.py              # Pipeline AI multi-modelo
│   └── tests/
│       ├── test_hexagonal_smoke.py          (2 tests)
│       ├── test_gis_smoke.py                (2 tests)
│       └── test_territorial_weather_climate_risk.py (13 tests — Fases 1-5)
├── frontend/
│   ├── Dockerfile / .dockerignore
│   └── src/
│       ├── App.jsx                    # 3 tabs: Mapa urbano, Mapa ICV, Métricas CO₂
│       ├── api/alba.js · api/gis.js
│       └── components/
│           ├── AnonymizerPanel.jsx    # Textarea + Anonimizar + 🎤 Voz
│           ├── MapPanel.jsx           # Leaflet, rutas Valencia
│           ├── GisMapPanel.jsx        # OpenLayers 10.9, capas ICV
│           ├── MetricsPanel.jsx       # Recharts, CO₂ antes/después
│           └── RouteList.jsx
├── docker-compose.yml
└── .gitignore
```

---

## Variables de entorno

Fichero: `backend/.env` (excluido de git por `.gitignore`).

```bash
# Groq — https://console.groq.com (gratuito: 14.400 req/día, <100ms latencia)
GROQ_API_KEY=gsk_...

# HuggingFace — https://huggingface.co/settings/tokens (token read gratuito)
# Modelo: BSC-LT/salamandra-7b-instruct (español soberano, ALIA Kit BSC)
HF_API_KEY=hf_...

# DeepSeek — https://platform.deepseek.com (opcional, fallback)
DEEPSEEK_API_KEY=sk-...

# HMAC — min 32 chars aleatorios
# Generar: python3 -c "import secrets; print(secrets.token_hex(32))"
HMAC_SECRET=...

# AEMET — https://opendata.aemet.es/centrodedescargas/altaUsuario (gratuita)
# Sin key: WeatherEngine devuelve fallback neutro, risk_level=low
AEMET_API_KEY=eyJ...

# ICV (público, sin autenticación requerida)
ICV_WMS_URL=http://terramapas.icv.gva.es/0105_Delimitaciones
ICV_WFS_URL=http://terramapas.icv.gva.es/0105_Delimitaciones
ICV_WMTS_URL=
GIS_TIMEOUT_SECONDS=15

# DS4M pesos (deben sumar 1.0 — ajustables por zona o temporada)
RISK_WEIGHT_HEAT=0.40
RISK_WEIGHT_FLOOD=0.30
RISK_WEIGHT_FIRE=0.20
RISK_WEIGHT_CO2=0.10
```

---

## API — 23 endpoints

```
GET  /api/health
GET  /api/docs     (Swagger UI)
GET  /api/redoc

POST /api/optimize/           → VRP Clarke-Wright + climate_risk
GET  /api/optimize/demo       → demo Valencia 103km→66km

POST /api/anonymize/          → pipeline AI: Groq→Salamandra→DeepSeek→HMAC
GET  /api/anonymize/demo

GET  /api/metrics/co2-factors → EU Reg. 2019/1242
GET  /api/metrics/impact

GET  /api/gis/catalog         → WMS+WMTS capas ICV
GET  /api/gis/wfs/features    → GeoJSON municipios/comarcas
GET  /api/gis/wms/proxy       → proxy teselas anti-CORS

GET  /api/territorial/context      ?lat=&lon=  → municipio, comarca, zona protegida
GET  /api/territorial/municipality ?lat=&lon=
GET  /api/territorial/comarca      ?lat=&lon=

GET  /api/weather/risk         ?lat=&lon=  → AEMET + riesgo determinista
GET  /api/weather/observation  ?lat=&lon=

GET  /api/climate/risk   ?lat=&lon=  → heat, fire, flood, drought (Copernicus IDW)
GET  /api/climate/heat   ?lat=&lon=
GET  /api/climate/fire   ?lat=&lon=
GET  /api/climate/flood  ?lat=&lon=

POST /api/risk/compute         body: {heat,flood,fire,co2} → DS4M score
GET  /api/risk/location  ?lat=&lon=&co2_index= → DS4M integrado
```

---

## Motor de riesgo DS4M — fórmula

```
risk_score = w_heat  × heat
           + w_flood × flood
           + w_fire  × fire
           + w_co2   × co2

Pesos por defecto (contexto CV mediterráneo verano):
  w_heat=0.40  w_flood=0.30  w_fire=0.20  w_co2=0.10

Clasificación:
  ≥0.80 → very_high | ≥0.60 → high | ≥0.40 → medium | ≥0.20 → low | <0.20 → very_low

heat_blended (en risk/location):
  0.70 × climate.heat_index + 0.30 × weather.heat_risk
  (combina ERA5-Land largo plazo con AEMET operativo)
```

---

## Algoritmo meteorológico determinista (sin IA)

```
heat_risk:   ≥40°C→1.0 | ≥36°C→0.80 | ≥32°C→0.55 | ≥27°C→0.25 | else→0.0
wind_risk:  ≥100→1.0  | ≥70→0.75  | ≥50→0.45  | ≥35→0.20  | else→0.0
storm_risk: (≥30mm/h + ≥50km/h)→1.0 | ≥15mm/h→0.65 | ≥5mm/h→0.30 | else→0.0
risk_score = 0.50×heat + 0.30×storm + 0.20×wind
```

---

## Zonas climáticas CV (15 zonas IDW — Copernicus 2024)

```
Zona                lat      lon     heat  fire  flood drought
Valencia ciudad     39.47  -0.38   0.72  0.25   0.45   0.60
L'Albufera          39.33  -0.35   0.68  0.15   0.90   0.55
Sierra Calderona    39.72  -0.55   0.65  0.85   0.10   0.50
Ribera Alta         39.13  -0.52   0.70  0.20   0.70   0.58
La Safor/Gandia     38.98  -0.18   0.65  0.30   0.40   0.52
Alacant ciudad      38.35  -0.49   0.80  0.35   0.30   0.75
El Baix Segura      38.05  -0.78   0.78  0.20   0.92   0.80
Font Roja/Alcoi     38.70  -0.47   0.62  0.70   0.15   0.55
Castelló de la P.   39.99   0.03   0.58  0.28   0.35   0.45
Els Ports/Morella   40.62  -0.10   0.50  0.92   0.05   0.42
El Maestrat         40.38  -0.02   0.52  0.65   0.10   0.48
Vega Baja/Orihuela  38.08  -0.93   0.92  0.40   0.60   0.88
La Marina Alta      38.84   0.11   0.68  0.45   0.25   0.62
La Vall d'Albaida   38.82  -0.53   0.66  0.55   0.20   0.58
Requena-Utiel       39.48  -1.10   0.70  0.78   0.08   0.72
Fuentes: ERA5-Land temp. superficial verano 2024 · EFFIS · PATRICOVA · SPI-3 AEMET
```

---

## VRP Fase 5 — función de coste con riesgo climático

```python
# Coste efectivo (i→j):
cost_eff(i→j) = haversine_km(i,j) × (1 + climate_risk_weight × risk_j)

# Ahorro efectivo:
savings(i,j) = cost_eff(depot→i) + cost_eff(depot→j) - cost_eff(i→j)

# Stop.climate_risk = DS4M RiskScore del punto j (0.0–1.0)
# climate_risk_weight=0.0 → comportamiento idéntico al original (backward-compatible)
```

---

## Capas ICV disponibles

```
Endpoint: http://terramapas.icv.gva.es/0105_Delimitaciones
Protocolos: WMS 1.3.0 + WFS 2.0.0

Capa                   typeNames WFS             Campos
ICV.Municipios         ms:ICV.Municipios         Nmun, Npro
ICV.Comarcas           ms:ICV.Comarcas           Ncomar
ICV.Provincias         ms:ICV.Provincias
ICV.ComunidadAutonoma  ms:ICV.ComunidadAutonoma
```

---

## Seguridad

| Vector | Medida |
|--------|--------|
| CORS | credentials=False, methods=[GET,POST], 6 orígenes explícitos |
| SSRF proxy WMS | whitelist 16 params OGC (_WMS_ALLOWED_PARAMS) |
| DoS anonimizador | field_validator: texto max 4000 chars, device_id max 64 |
| Model injection | whitelist: alia_groq_joint, salamandra, groq, auto |
| HMAC_SECRET | @field_validator min 32 chars, detecta centinela dev |
| PHI | HMAC-SHA256(valor + device_id + fecha_ISO) — no reversible |
| Docker | .dockerignore excluye .env en backend y frontend |
| Git | .gitignore: .env, __pycache__, .venv, node_modules, dist/ |

---

## Tests — 17 passed

```bash
cd backend && python3 -m pytest tests/ -q   # ~5s, 0 dependencies externas
```

| Fichero | N | Qué verifica |
|---------|---|--------------|
| test_hexagonal_smoke.py | 2 | Anonimización alia_groq_joint |
| test_gis_smoke.py | 2 | Catálogo ICV, WFS vacío |
| test_territorial_weather_climate_risk.py | 13 | Fases 1-5 sin red |

---

## Despliegue Docker

```bash
cp backend/.env.example backend/.env   # rellenar keys
docker-compose up --build
# http://localhost:5175  → Frontend
# http://localhost:8001  → Backend
# http://localhost:8001/api/docs → Swagger
```

`HMAC_SECRET` es obligatorio en docker-compose (`:?` — falla si falta).  
Variables ICV tienen defaults públicos embebidos.

---

## Dependencias

```
Backend Python:          Frontend npm:
fastapi >=0.111          react 18.3.1
uvicorn[standard]        vite 8.1.0 (0 CVEs)
httpx >=0.27             leaflet 1.9.4
pydantic >=2.7           ol 10.9.0 (OpenLayers)
pydantic-settings >=2.2  recharts 2.12.7
python-dotenv >=1.0
```

---

## Patrón para añadir nueva fuente

```
1. app/domain/entities/mi_entidad.py       ← dataclass frozen=True + to_dict()
2. app/domain/ports/mi_port.py             ← ABC con métodos abstractos
3. app/infrastructure/adapters/mi_adapter.py ← implementación concreta
4. app/services/mi_service.py              ← orquestación del port
5. app/use_cases/mi_use_case.py            ← validación + delegación al servicio
6. routes/mi_router.py                     ← FastAPI router
7. main.py: app.include_router(mi_router, prefix="/api/mi", tags=["Mi Engine"])
8. tests/test_mi_smoke.py                  ← al menos 2 tests sin red
```

---

## Contexto del proyecto

Hackathon IABiomed 2 · Valencia · 2026  
Stack soberano: Salamandra-7B (BSC, proyecto ALIA gobierno español) como motor NLP primario  
Regulaciones: RGPD · EU Reg. 2019/1242 (CO₂) · PATRICOVA (inundaciones CV)  
Fuentes públicas verificadas: ICV (libre) · AEMET OpenData (gratuita) · Copernicus CDS (gratuito)
