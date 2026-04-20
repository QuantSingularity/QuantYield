import { useState } from "react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from "recharts";
import {
  mlForecast,
  regimeData,
  garchData,
  pcaData,
  chartColors,
} from "../../data/mockData";
import { useToast } from "../../context/ToastContext";

const Tip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "#111927",
        border: "1px solid rgba(99,120,180,0.3)",
        borderRadius: 8,
        padding: "9px 12px",
        fontSize: 11,
      }}
    >
      <div
        style={{
          color: "#8898b8",
          marginBottom: 4,
          fontFamily: "var(--font-mono)",
        }}
      >
        {label}
      </div>
      {payload
        .filter((p) => p.value != null)
        .map((p) => (
          <div
            key={p.name}
            style={{
              color: p.color || "#f0f4ff",
              fontFamily: "var(--font-mono)",
              fontWeight: 600,
              marginBottom: 2,
            }}
          >
            {p.name}: {+p.value}%
          </div>
        ))}
    </div>
  );
};

const MODELS = [
  {
    id: "forecaster",
    emoji: "📈",
    name: "Rate Forecaster",
    desc: "Transformer / LSTM / AR(1)",
    color: chartColors.indigo,
    status: "Transformer",
  },
  {
    id: "regime",
    emoji: "🔍",
    name: "Regime Classifier",
    desc: "RF + XGBoost Ensemble",
    color: chartColors.violet,
    status: "RF+XGB",
  },
  {
    id: "garch",
    emoji: "📊",
    name: "GARCH Volatility",
    desc: "GARCH(1,1) / EGARCH",
    color: chartColors.amber,
    status: "GARCH(1,1)",
  },
  {
    id: "credit",
    emoji: "⚡",
    name: "Credit Spread",
    desc: "XGBoost OAS Prediction",
    color: chartColors.red,
    status: "XGBoost",
  },
  {
    id: "pca",
    emoji: "🔬",
    name: "PCA Factors",
    desc: "Level · Slope · Curvature",
    color: chartColors.teal,
    status: "Active",
  },
];

const REGIME_COLORS = {
  inverted: chartColors.red,
  flat: chartColors.amber,
  normal: chartColors.green,
  steep: chartColors.indigo,
  humped: chartColors.violet,
};
const FEAT_COLORS = [
  chartColors.indigo,
  chartColors.teal,
  chartColors.amber,
  chartColors.violet,
  chartColors.green,
  chartColors.red,
];

export default function ML() {
  const toast = useToast();
  const [active, setActive] = useState("forecaster");

  const fctData = mlForecast.labels.map((d, i) => ({
    date: d.slice(5),
    Upper: +(mlForecast.upper[i] * 100).toFixed(3),
    Point: +(mlForecast.point[i] * 100).toFixed(3),
    Lower: +(mlForecast.lower[i] * 100).toFixed(3),
  }));

  const garchChart = garchData.labels.map((d, i) => ({
    date: d.slice(5),
    Vol: garchData.vol[i],
  }));

  const pcaTenors = Object.keys(pcaData.loadings.Level);
  const pcaChart = pcaTenors.map((t) => ({
    tenor: t,
    Level: pcaData.loadings.Level[t],
    Slope: pcaData.loadings.Slope[t],
    Curvature: pcaData.loadings.Curvature[t],
  }));
  const pcaVarChart = pcaData.factors.map((f, i) => ({
    name: f,
    value: +(pcaData.variance[i] * 100).toFixed(1),
  }));

  const creditFeats = {
    Duration: 0.34,
    "Credit Rating": 0.28,
    "YTM Level": 0.18,
    "Coupon Rate": 0.12,
    "Face Value": 0.08,
  };
  const creditFeatChart = Object.entries(creditFeats).map(([n, v]) => ({
    name: n,
    value: +(v * 100).toFixed(1),
  }));

  const regimeProbs = Object.entries(regimeData.probs).map(([r, p]) => ({
    regime: r,
    prob: +(p * 100).toFixed(1),
  }));
  const regimeFeatChart = Object.entries(regimeData.features).map(([n, v]) => ({
    name: n,
    value: +(v * 100).toFixed(1),
  }));

  return (
    <>
      {/* Model selector */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(5,1fr)",
          gap: 12,
          marginBottom: 24,
        }}
      >
        {MODELS.map((m) => (
          <div
            key={m.id}
            onClick={() => setActive(m.id)}
            className="card"
            style={{
              cursor: "pointer",
              transition: "all 0.18s",
              borderColor: active === m.id ? m.color : undefined,
              boxShadow: active === m.id ? `0 0 20px ${m.color}30` : undefined,
              background: active === m.id ? `${m.color}08` : undefined,
            }}
          >
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: "var(--r-md)",
                background: `${m.color}18`,
                border: `1px solid ${m.color}30`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 18,
                marginBottom: 10,
              }}
            >
              {m.emoji}
            </div>
            <div
              style={{
                fontFamily: "var(--font-head)",
                fontSize: 12.5,
                fontWeight: 700,
                color: "var(--text-primary)",
                marginBottom: 2,
              }}
            >
              {m.name}
            </div>
            <div
              style={{
                fontSize: 10,
                color: "var(--text-muted)",
                lineHeight: 1.4,
                marginBottom: 10,
              }}
            >
              {m.desc}
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                fontSize: 10,
                fontWeight: 600,
                color: "var(--green)",
              }}
            >
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: "var(--green)",
                  boxShadow: "0 0 4px var(--green)",
                  display: "inline-block",
                }}
              />
              {m.status}
            </div>
          </div>
        ))}
      </div>

      {/* Forecaster */}
      {active === "forecaster" && (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "2fr 1fr",
              gap: 16,
              marginBottom: 16,
            }}
          >
            <div className="card">
              <div className="card-header">
                <span className="card-title">
                  10Y UST Rate Forecast — 60-Day Horizon
                </span>
                <div style={{ display: "flex", gap: 6 }}>
                  <span className="badge badge-indigo">Transformer</span>
                  <span className="badge badge-teal">90% CI</span>
                </div>
              </div>
              <div
                style={{
                  display: "flex",
                  gap: 10,
                  marginBottom: 10,
                  flexWrap: "wrap",
                }}
              >
                {[
                  [
                    "Current",
                    (mlForecast.point[0] * 100).toFixed(3) + "%",
                    chartColors.indigo,
                  ],
                  [
                    "60d Target",
                    (mlForecast.point[60] * 100).toFixed(3) + "%",
                    chartColors.teal,
                  ],
                  [
                    "Upper 90%",
                    (mlForecast.upper[60] * 100).toFixed(3) + "%",
                    chartColors.red,
                  ],
                  [
                    "Lower 90%",
                    (mlForecast.lower[60] * 100).toFixed(3) + "%",
                    chartColors.green,
                  ],
                ].map(([l, v, c]) => (
                  <div
                    key={l}
                    style={{
                      padding: "4px 11px",
                      borderRadius: "var(--r-full)",
                      fontFamily: "var(--font-mono)",
                      fontSize: 11,
                      fontWeight: 600,
                      background: `${c}18`,
                      color: c,
                      border: `1px solid ${c}30`,
                    }}
                  >
                    {l}: {v}
                  </div>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart
                  data={fctData}
                  margin={{ top: 4, right: 10, bottom: 0, left: 0 }}
                >
                  <defs>
                    <linearGradient id="fg" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="5%"
                        stopColor={chartColors.indigo}
                        stopOpacity={0.2}
                      />
                      <stop
                        offset="95%"
                        stopColor={chartColors.indigo}
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(99,120,180,0.12)"
                  />
                  <XAxis
                    dataKey="date"
                    tick={{
                      fill: "#4e6080",
                      fontSize: 10,
                      fontFamily: "var(--font-mono)",
                    }}
                    interval={9}
                  />
                  <YAxis
                    tick={{
                      fill: "#4e6080",
                      fontSize: 10,
                      fontFamily: "var(--font-mono)",
                    }}
                    tickFormatter={(v) => v + "%"}
                    domain={["auto", "auto"]}
                  />
                  <Tooltip content={<Tip />} />
                  <Area
                    type="monotone"
                    dataKey="Upper"
                    stroke="transparent"
                    fill={chartColors.indigo}
                    fillOpacity={0.1}
                  />
                  <Area
                    type="monotone"
                    dataKey="Point"
                    stroke={chartColors.indigo}
                    strokeWidth={2.5}
                    fill="url(#fg)"
                  />
                  <Area
                    type="monotone"
                    dataKey="Lower"
                    stroke="transparent"
                    fill="transparent"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 14 }}>
                Architecture
              </div>
              <div className="stat-list">
                {[
                  ["Backend", "Transformer", "accent"],
                  ["Fallback 1", "LSTM", ""],
                  ["Fallback 2", "AR(1)", "muted"],
                  ["Lookback", "20 days", ""],
                  ["d_model", "64", ""],
                  ["Attn. Heads", "4", ""],
                  ["Encoder Layers", "2", ""],
                  ["Optimizer", "AdamW", ""],
                  ["LR Schedule", "Cosine", ""],
                  ["Loss", "HuberLoss", ""],
                  ["MC Simulations", "500", ""],
                  ["Epochs", "60", ""],
                ].map(([k, v, c]) => (
                  <div key={k} className="stat-row">
                    <span className="stat-key">{k}</span>
                    <span className={`stat-val ${c || ""}`}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}
          >
            <div className="card">
              <div className="card-title" style={{ marginBottom: 12 }}>
                Configure Forecast
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 12,
                  marginBottom: 12,
                }}
              >
                <div className="form-group">
                  <label className="form-label">Horizon (days)</label>
                  <input
                    type="number"
                    className="form-control"
                    defaultValue={60}
                    min={1}
                    max={252}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Backend</label>
                  <select className="form-control">
                    <option>transformer</option>
                    <option>lstm</option>
                    <option>ar1</option>
                  </select>
                </div>
              </div>
              <button
                className="btn btn-primary"
                onClick={() =>
                  toast(
                    "POST /api/v1/curves/{id}/forecast/ · Transformer active",
                    "success",
                  )
                }
              >
                Run Forecast
              </button>
            </div>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 12 }}>
                LSTM Architecture
              </div>
              <div className="stat-list">
                {[
                  ["LSTM Layers", "2"],
                  ["Hidden Size", "64"],
                  ["Dropout", "0.1"],
                  ["Loss", "MSELoss"],
                  ["Optimizer", "Adam"],
                ].map(([k, v]) => (
                  <div key={k} className="stat-row">
                    <span className="stat-key">{k}</span>
                    <span className="stat-val">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Regime */}
      {active === "regime" && (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "2fr 1fr",
              gap: 16,
              marginBottom: 16,
            }}
          >
            <div className="card">
              <div className="card-header">
                <span className="card-title">Regime Probabilities</span>
                <span className={`regime-chip regime-${regimeData.regime}`}>
                  {regimeData.regime.toUpperCase()}
                </span>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart
                  data={regimeProbs}
                  margin={{ top: 4, right: 10, bottom: 0, left: 0 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(99,120,180,0.12)"
                  />
                  <XAxis
                    dataKey="regime"
                    tick={{
                      fill: "#4e6080",
                      fontSize: 10,
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <YAxis
                    tick={{
                      fill: "#4e6080",
                      fontSize: 10,
                      fontFamily: "var(--font-mono)",
                    }}
                    tickFormatter={(v) => v + "%"}
                  />
                  <Tooltip content={<Tip />} />
                  <Bar
                    dataKey="prob"
                    name="Probability %"
                    radius={[4, 4, 0, 0]}
                  >
                    {regimeProbs.map((_, i) => (
                      <Cell
                        key={i}
                        fill={Object.values(REGIME_COLORS)[i]}
                        fillOpacity={0.8}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(5,1fr)",
                  gap: 8,
                  marginTop: 14,
                }}
              >
                {regimeProbs.map((r) => (
                  <div
                    key={r.regime}
                    style={{
                      textAlign: "center",
                      background: "var(--bg-overlay)",
                      border: `1px solid ${REGIME_COLORS[r.regime]}30`,
                      borderRadius: "var(--r-md)",
                      padding: "8px 6px",
                    }}
                  >
                    <div
                      style={{
                        fontSize: 9.5,
                        color: "var(--text-muted)",
                        fontWeight: 600,
                        textTransform: "uppercase",
                        marginBottom: 3,
                      }}
                    >
                      {r.regime}
                    </div>
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 18,
                        fontWeight: 700,
                        color: REGIME_COLORS[r.regime],
                      }}
                    >
                      {r.prob}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 14 }}>
                Model Info
              </div>
              <div className="stat-list">
                {[
                  ["Algorithm", "RF + XGBoost", "accent"],
                  ["Regime Labels", "5", ""],
                  ["Active", "inverted", "neg"],
                  ["Confidence", "87%", "pos"],
                  ["Slope 2s10s", "−48.6bp", "neg"],
                  ["Butterfly", "12.4bp", ""],
                ].map(([k, v, c]) => (
                  <div key={k} className="stat-row">
                    <span className="stat-key">{k}</span>
                    <span className={`stat-val ${c || ""}`}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-title" style={{ marginBottom: 14 }}>
              Feature Importances
            </div>
            {regimeFeatChart.map((f, i) => (
              <div key={f.name} className="alloc-row">
                <span className="alloc-label">{f.name}</span>
                <div className="alloc-track">
                  <div
                    className="alloc-fill"
                    style={{
                      width: f.value + "%",
                      background: FEAT_COLORS[i % FEAT_COLORS.length],
                    }}
                  />
                </div>
                <span className="alloc-pct">{f.value}%</span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* GARCH */}
      {active === "garch" && (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "2fr 1fr",
              gap: 16,
              marginBottom: 16,
            }}
          >
            <div className="card">
              <div className="card-header">
                <span className="card-title">
                  GARCH(1,1) Volatility Forecast — 30 Days
                </span>
                <span className="badge badge-amber">GARCH(1,1)</span>
              </div>
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart
                  data={garchChart}
                  margin={{ top: 4, right: 10, bottom: 0, left: 0 }}
                >
                  <defs>
                    <linearGradient id="gg" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="5%"
                        stopColor={chartColors.amber}
                        stopOpacity={0.2}
                      />
                      <stop
                        offset="95%"
                        stopColor={chartColors.amber}
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(99,120,180,0.12)"
                  />
                  <XAxis
                    dataKey="date"
                    tick={{
                      fill: "#4e6080",
                      fontSize: 10,
                      fontFamily: "var(--font-mono)",
                    }}
                    interval={5}
                  />
                  <YAxis
                    tick={{
                      fill: "#4e6080",
                      fontSize: 10,
                      fontFamily: "var(--font-mono)",
                    }}
                    tickFormatter={(v) => v + "%"}
                  />
                  <Tooltip content={<Tip />} />
                  <Area
                    type="monotone"
                    dataKey="Vol"
                    name="Vol %"
                    stroke={chartColors.amber}
                    strokeWidth={2.5}
                    fill="url(#gg)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 14 }}>
                GARCH Parameters
              </div>
              <div
                style={{
                  background: "var(--bg-overlay)",
                  borderRadius: "var(--r-md)",
                  padding: 11,
                  marginBottom: 12,
                  fontFamily: "var(--font-mono)",
                  fontSize: 10.5,
                  color: "var(--text-muted)",
                  lineHeight: 1.8,
                }}
              >
                σ²ₜ = ω + α·ε²ₜ₋₁ + β·σ²ₜ₋₁
              </div>
              <div className="stat-list">
                {[
                  ["ω (intercept)", garchData.omega.toFixed(6), "accent"],
                  ["α (ARCH)", garchData.alpha.toFixed(4), ""],
                  ["β (GARCH)", garchData.beta.toFixed(4), ""],
                  [
                    "α+β (persist)",
                    (garchData.alpha + garchData.beta).toFixed(4),
                    "pos",
                  ],
                  ["Primary", "GARCH(1,1)", ""],
                  ["Alt Model", "EGARCH", ""],
                  ["Fallback", "Hist. Rolling", "muted"],
                ].map(([k, v, c]) => (
                  <div key={k} className="stat-row">
                    <span className="stat-key">{k}</span>
                    <span className={`stat-val ${c || ""}`}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-title" style={{ marginBottom: 14 }}>
              Volatility Term Structure
            </div>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart
                data={[
                  ["1M", 0.621],
                  ["3M", 0.587],
                  ["6M", 0.542],
                  ["1Y", 0.512],
                  ["2Y", 0.489],
                  ["3Y", 0.471],
                  ["5Y", 0.458],
                  ["10Y", 0.442],
                ].map(([t, v]) => ({ tenor: t, vol: v }))}
                margin={{ top: 4, right: 10, bottom: 0, left: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(99,120,180,0.12)"
                />
                <XAxis
                  dataKey="tenor"
                  tick={{
                    fill: "#4e6080",
                    fontSize: 10,
                    fontFamily: "var(--font-mono)",
                  }}
                />
                <YAxis
                  tick={{
                    fill: "#4e6080",
                    fontSize: 10,
                    fontFamily: "var(--font-mono)",
                  }}
                  tickFormatter={(v) => v + "%"}
                />
                <Tooltip content={<Tip />} />
                <Bar
                  dataKey="vol"
                  name="Impl. Vol %"
                  fill={chartColors.amber}
                  fillOpacity={0.7}
                  radius={[3, 3, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {/* Credit Spread */}
      {active === "credit" && (
        <div
          style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}
        >
          <div className="card">
            <div className="card-header">
              <span className="card-title">XGBoost OAS Prediction</span>
              <span className="badge badge-red">XGBoost</span>
            </div>
            <div
              style={{
                textAlign: "center",
                padding: "20px 0 24px",
                borderBottom: "1px solid var(--border)",
                marginBottom: 16,
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  color: "var(--text-muted)",
                  marginBottom: 6,
                }}
              >
                Predicted OAS
              </div>
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 52,
                  fontWeight: 700,
                  color: "var(--red)",
                  lineHeight: 1,
                }}
              >
                32.4
              </div>
              <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                basis points
              </div>
              <div style={{ marginTop: 10 }}>
                <span className="badge badge-green">R² = 0.8921</span>
              </div>
            </div>
            <div className="card-title" style={{ marginBottom: 10 }}>
              Input Features
            </div>
            <div className="stat-list">
              {[
                ["Duration", "8.12"],
                ["YTM", "4.621%"],
                ["Coupon", "4.500%"],
                ["Rating Score", "1 (AAA)"],
                ["Log Face Value", "6.000"],
              ].map(([k, v]) => (
                <div key={k} className="stat-row">
                  <span className="stat-key">{k}</span>
                  <span className="stat-val">{v}</span>
                </div>
              ))}
            </div>
            <div className="divider" />
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 10,
                marginBottom: 14,
              }}
            >
              <div className="form-group">
                <label className="form-label">Duration</label>
                <input
                  type="number"
                  className="form-control"
                  defaultValue={8.12}
                  step={0.1}
                />
              </div>
              <div className="form-group">
                <label className="form-label">YTM (decimal)</label>
                <input
                  type="number"
                  className="form-control"
                  defaultValue={0.04621}
                  step={0.001}
                />
              </div>
            </div>
            <button
              className="btn btn-primary btn-sm"
              onClick={() =>
                toast(
                  "Credit OAS predicted: 34.2bp · XGBoost · Fallback: Random Forest",
                  "success",
                )
              }
            >
              Predict OAS
            </button>
          </div>
          <div className="card">
            <div className="card-title" style={{ marginBottom: 14 }}>
              Feature Importances
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={creditFeatChart}
                layout="vertical"
                margin={{ top: 4, right: 10, bottom: 0, left: 80 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(99,120,180,0.12)"
                />
                <XAxis
                  type="number"
                  tick={{
                    fill: "#4e6080",
                    fontSize: 10,
                    fontFamily: "var(--font-mono)",
                  }}
                  tickFormatter={(v) => v + "%"}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fill: "#8898b8", fontSize: 10.5 }}
                  width={80}
                />
                <Tooltip content={<Tip />} />
                <Bar dataKey="value" name="Importance %" radius={[0, 3, 3, 0]}>
                  {creditFeatChart.map((_, i) => (
                    <Cell key={i} fill={FEAT_COLORS[i]} fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="divider" />
            <div className="card-title" style={{ marginBottom: 10 }}>
              Fallback Hierarchy
            </div>
            <div className="stat-list">
              {[
                ["Primary", "XGBoost", "accent"],
                ["Fallback", "Random Forest", ""],
                ["Last Resort", "Rating Table Lookup", "muted"],
              ].map(([k, v, c]) => (
                <div key={k} className="stat-row">
                  <span className="stat-key">{k}</span>
                  <span className={`stat-val ${c || ""}`}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* PCA */}
      {active === "pca" && (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "2fr 1fr",
              gap: 16,
              marginBottom: 16,
            }}
          >
            <div className="card">
              <div className="card-header">
                <span className="card-title">PCA Factor Loadings</span>
                <span className="badge badge-teal">
                  Level · Slope · Curvature
                </span>
              </div>
              <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
                {[
                  ["Level", chartColors.indigo],
                  ["Slope", chartColors.teal],
                  ["Curvature", chartColors.amber],
                ].map(([l, c]) => (
                  <div key={l} className="legend-item">
                    <div className="legend-dot" style={{ background: c }} />
                    <span>{l}</span>
                  </div>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart
                  data={pcaChart}
                  margin={{ top: 4, right: 10, bottom: 0, left: 0 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(99,120,180,0.12)"
                  />
                  <XAxis
                    dataKey="tenor"
                    tick={{
                      fill: "#4e6080",
                      fontSize: 10,
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <YAxis
                    tick={{
                      fill: "#4e6080",
                      fontSize: 10,
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <Tooltip content={<Tip />} />
                  <Line
                    type="monotone"
                    dataKey="Level"
                    stroke={chartColors.indigo}
                    strokeWidth={2.5}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="Slope"
                    stroke={chartColors.teal}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="Curvature"
                    stroke={chartColors.amber}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 14 }}>
                Variance Explained
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 8,
                  marginBottom: 16,
                }}
              >
                {pcaData.factors.map((f, i) => (
                  <div
                    key={f}
                    style={{
                      textAlign: "center",
                      background: "var(--bg-overlay)",
                      border: `1px solid ${[chartColors.indigo, chartColors.teal, chartColors.amber, "rgba(99,120,180,0.2)"][i]}30`,
                      borderRadius: "var(--r-md)",
                      padding: "10px 8px",
                    }}
                  >
                    <div
                      style={{
                        fontSize: 9.5,
                        color: "var(--text-muted)",
                        fontWeight: 600,
                        marginBottom: 4,
                      }}
                    >
                      {f}
                    </div>
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 20,
                        fontWeight: 700,
                        color: [
                          chartColors.indigo,
                          chartColors.teal,
                          chartColors.amber,
                          "var(--text-muted)",
                        ][i],
                      }}
                    >
                      {(pcaData.variance[i] * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
              <div className="card-title" style={{ marginBottom: 10 }}>
                Current Factor Scores
              </div>
              <div className="stat-list">
                {[
                  ["Level", "4.81%", "accent"],
                  ["Slope", "−0.486bp", "neg"],
                  ["Curvature", "1.24bp", ""],
                ].map(([k, v, c]) => (
                  <div key={k} className="stat-row">
                    <span className="stat-key">{k}</span>
                    <span className={`stat-val ${c}`}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Loading matrix */}
          <div className="card">
            <div className="card-title" style={{ marginBottom: 14 }}>
              Factor Loading Matrix
            </div>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Factor</th>
                    {Object.keys(pcaData.loadings.Level).map((t) => (
                      <th key={t} className="text-right">
                        {t}
                      </th>
                    ))}
                    <th className="text-right">Interpretation</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(pcaData.loadings).map(([fac, loads], fi) => (
                    <tr key={fac}>
                      <td>
                        <span
                          className={`badge ${["badge-indigo", "badge-teal", "badge-amber"][fi]}`}
                        >
                          {fac}
                        </span>
                      </td>
                      {Object.values(loads).map((v, i) => (
                        <td
                          key={i}
                          className="text-right mono"
                          style={{
                            fontSize: 11,
                            color: v >= 0 ? "var(--green)" : "var(--red)",
                          }}
                        >
                          {v >= 0 ? "+" : ""}
                          {v.toFixed(3)}
                        </td>
                      ))}
                      <td
                        className="text-right"
                        style={{ fontSize: 10.5, color: "var(--text-muted)" }}
                      >
                        {
                          [
                            "Parallel shift",
                            "Short vs long twist",
                            "Medium hump/trough",
                          ][fi]
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </>
  );
}
