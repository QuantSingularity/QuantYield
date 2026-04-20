import { useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from "recharts";
import {
  benchmarkSpreads,
  history10y,
  history2y,
  history5y,
  fmt,
  ratingBadge,
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
      {payload.map((p) => (
        <div
          key={p.name}
          style={{
            color: p.color || "#f0f4ff",
            fontFamily: "var(--font-mono)",
            fontWeight: 600,
            marginBottom: 2,
          }}
        >
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
};

function calcDirtyPrice(F, c, ytm, T, m) {
  if (m === 0) return F / Math.pow(1 + ytm, T);
  const r = ytm / m,
    n = Math.round(T * m),
    coupon = (c / m) * F;
  if (r === 0) return coupon * n + F;
  return (coupon * (1 - Math.pow(1 + r, -n))) / r + F * Math.pow(1 + r, -n);
}

function calcMetrics(F, c, ytm, T, m) {
  const r = ytm / m,
    n = Math.round(T * m),
    coupon = (c / m) * F;
  const dirty = calcDirtyPrice(F, c, ytm, T, m);
  let macNum = 0;
  for (let i = 1; i <= n; i++) {
    const cf = i < n ? coupon : coupon + F;
    macNum += ((i / m) * cf) / Math.pow(1 + r, i);
  }
  const mac = macNum / dirty;
  const mod = mac / (1 + ytm / m);
  let cv = 0;
  for (let i = 1; i <= n; i++) {
    const cf = i < n ? coupon : coupon + F;
    cv += (cf * i * (i + 1)) / Math.pow(1 + r, i + 2);
  }
  return {
    dirty: dirty / 10,
    mac,
    mod,
    conv: cv / (dirty * m * m),
    dv01: (dirty * mod * 0.0001) / 100,
  };
}

export default function Analytics() {
  const toast = useToast();
  const [tab, setTab] = useState("pricer");

  // Pricer state
  const [pf, setPF] = useState({ F: 1000, c: 0.045, ytm: 0.05, T: 10, m: 2 });
  const [pyData, setPYData] = useState(null);
  const [metrics, setMetrics] = useState(null);

  const runPricer = () => {
    const m = calcMetrics(pf.F, pf.c, pf.ytm, pf.T, pf.m);
    setMetrics(m);
    const data = [];
    for (let y = 0.01; y <= 0.12; y += 0.002) {
      data.push({
        ytm: (y * 100).toFixed(2) + "%",
        Price: +(calcDirtyPrice(pf.F, pf.c, y, pf.T, pf.m) / 10).toFixed(3),
      });
    }
    setPYData(data);
  };

  // Duration approx state
  const [da, setDA] = useState({ P: 98.234, D: 7.94, C: 72.3, shift: 100 });
  const daShift = da.shift / 10000;
  const daResult = {
    durPnL: da.P * -da.D * daShift,
    convPnL: da.P * 0.5 * da.C * daShift * daShift,
  };
  const daChartData = [];
  for (let s = -300; s <= 300; s += 20) {
    const dy = s / 10000;
    daChartData.push({
      shift: s + "bp",
      "Duration Only": +(da.P * -da.D * dy).toFixed(3),
      "Dur+Convexity": +(da.P * (-da.D * dy + 0.5 * da.C * dy * dy)).toFixed(3),
    });
  }

  const TABS = [
    ["pricer", "Quick Pricer"],
    ["da", "Duration Approx"],
    ["spreads", "Benchmark Spreads"],
    ["vol", "Rolling Volatility"],
    ["history", "Yield History"],
  ];

  const histData = history10y.labels.slice(-120).map((d, i) => ({
    date: d.slice(5),
    "10Y": +(history10y.rates.slice(-120)[i] * 100).toFixed(3),
    "2Y": +(history2y.rates.slice(-120)[i] * 100).toFixed(3),
    "5Y": +(history5y.rates.slice(-120)[i] * 100).toFixed(3),
  }));

  // rolling vol
  const volData = history10y.rates.slice(-90).map((r, i, arr) => {
    if (i < 20)
      return { date: history10y.labels.slice(-90)[i].slice(5), vol: null };
    const window = arr.slice(i - 20, i);
    const mean = window.reduce((a, b) => a + b, 0) / 20;
    const variance = window.reduce((a, b) => a + (b - mean) ** 2, 0) / 20;
    return {
      date: history10y.labels.slice(-90)[i].slice(5),
      vol: +(Math.sqrt(variance * 252) * 100).toFixed(3),
    };
  });

  return (
    <>
      <div className="tab-list">
        {TABS.map(([k, l]) => (
          <button
            key={k}
            className={`tab-trigger ${tab === k ? "active" : ""}`}
            onClick={() => setTab(k)}
          >
            {l}
          </button>
        ))}
      </div>

      {/* Quick Pricer */}
      {tab === "pricer" && (
        <div
          style={{ display: "grid", gridTemplateColumns: "1fr 1.6fr", gap: 18 }}
        >
          <div className="card">
            <div className="card-title" style={{ marginBottom: 16 }}>
              Bond Pricer — POST /api/v1/analytics/quick-price/
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {[
                ["Face Value ($)", "F", "number", 100],
                ["Annual Coupon Rate", "c", "number", 0.001],
                ["YTM (decimal)", "ytm", "number", 0.001],
                ["Years to Maturity", "T", "number", 0.5],
              ].map(([l, k, t, step]) => (
                <div key={k} className="form-group">
                  <label className="form-label">{l}</label>
                  <input
                    type={t}
                    className="form-control"
                    value={pf[k]}
                    step={step}
                    onChange={(e) =>
                      setPF((f) => ({ ...f, [k]: +e.target.value }))
                    }
                  />
                </div>
              ))}
              <div className="form-group">
                <label className="form-label">Coupon Frequency</label>
                <select
                  className="form-control"
                  value={pf.m}
                  onChange={(e) => setPF((f) => ({ ...f, m: +e.target.value }))}
                >
                  <option value={2}>Semiannual</option>
                  <option value={1}>Annual</option>
                  <option value={4}>Quarterly</option>
                  <option value={12}>Monthly</option>
                </select>
              </div>
              <button className="btn btn-primary" onClick={runPricer}>
                Calculate
              </button>
            </div>
            {metrics && (
              <div
                style={{
                  marginTop: 14,
                  background: "var(--bg-overlay)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--r-lg)",
                  padding: 14,
                }}
              >
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 10,
                  }}
                >
                  {[
                    [
                      "Dirty Price",
                      metrics.dirty.toFixed(3),
                      "var(--text-primary)",
                    ],
                    ["Macaulay Dur", metrics.mac.toFixed(3) + "Y", ""],
                    ["Modified Dur", metrics.mod.toFixed(3), ""],
                    ["Convexity", metrics.conv.toFixed(2), ""],
                    ["DV01", metrics.dv01.toFixed(2), "var(--amber)"],
                    ["PV01", (metrics.dv01 / 10).toFixed(3), ""],
                  ].map(([l, v, c]) => (
                    <div key={l} style={{ textAlign: "center" }}>
                      <div
                        style={{
                          fontSize: 9.5,
                          fontWeight: 600,
                          textTransform: "uppercase",
                          letterSpacing: "0.07em",
                          color: "var(--text-muted)",
                          marginBottom: 4,
                        }}
                      >
                        {l}
                      </div>
                      <div
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: 18,
                          fontWeight: 700,
                          color: c || "var(--teal-400)",
                        }}
                      >
                        {v}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className="card">
            <div className="card-title" style={{ marginBottom: 12 }}>
              Price–Yield Relationship
            </div>
            {pyData ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={pyData}
                  margin={{ top: 4, right: 10, bottom: 0, left: 0 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(99,120,180,0.12)"
                  />
                  <XAxis
                    dataKey="ytm"
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
                  />
                  <Tooltip content={<Tip />} />
                  <Line
                    type="monotone"
                    dataKey="Price"
                    stroke={chartColors.indigo}
                    strokeWidth={2.5}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">📉</div>
                <div className="empty-state-title">Click Calculate</div>
                <div className="empty-state-desc">
                  Enter bond parameters and calculate to see the price–yield
                  curve
                </div>
              </div>
            )}
            <div
              style={{
                marginTop: 12,
                fontSize: 11,
                color: "var(--text-muted)",
                lineHeight: 1.6,
              }}
            >
              Classic inverse price–yield relationship. The curvature represents
              convexity — the Taylor expansion underestimates price recovery for
              large yield drops.
            </div>
          </div>
        </div>
      )}

      {/* Duration Approx */}
      {tab === "da" && (
        <div
          style={{ display: "grid", gridTemplateColumns: "1fr 1.6fr", gap: 18 }}
        >
          <div className="card">
            <div className="card-title" style={{ marginBottom: 16 }}>
              Duration Approximation — POST
              /api/v1/analytics/duration-approximation/
            </div>
            <div
              style={{
                background: "var(--bg-overlay)",
                borderRadius: "var(--r-md)",
                padding: 11,
                marginBottom: 14,
                fontFamily: "var(--font-mono)",
                fontSize: 10.5,
                color: "var(--text-muted)",
                lineHeight: 1.8,
              }}
            >
              dP ≈ P × (−D_mod × dy + ½ × C × dy²)
            </div>
            {[
              ["Dirty Price", "P", "number", 0.001],
              ["Modified Duration", "D", "number", 0.01],
              ["Convexity", "C", "number", 0.1],
            ].map(([l, k, t, step]) => (
              <div key={k} className="form-group" style={{ marginBottom: 12 }}>
                <label className="form-label">{l}</label>
                <input
                  type={t}
                  className="form-control"
                  value={da[k]}
                  step={step}
                  onChange={(e) =>
                    setDA((f) => ({ ...f, [k]: +e.target.value }))
                  }
                />
              </div>
            ))}
            <div className="form-group" style={{ marginBottom: 16 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: 6,
                }}
              >
                <label className="form-label">Yield Shift</label>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 12,
                    color: "var(--teal-400)",
                  }}
                >
                  {da.shift > 0 ? "+" : ""}
                  {da.shift}bp
                </span>
              </div>
              <input
                type="range"
                className="slider"
                min={-300}
                max={300}
                value={da.shift}
                step={5}
                onChange={(e) =>
                  setDA((f) => ({ ...f, shift: +e.target.value }))
                }
              />
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 10,
                  color: "var(--text-muted)",
                  marginTop: 3,
                }}
              >
                <span>−300bp</span>
                <span>+300bp</span>
              </div>
            </div>
            <div
              style={{
                background: "var(--bg-overlay)",
                border: "1px solid var(--border)",
                borderRadius: "var(--r-lg)",
                padding: 14,
              }}
            >
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr",
                  gap: 10,
                  textAlign: "center",
                }}
              >
                {[
                  [
                    "Duration P&L",
                    daResult.durPnL,
                    daResult.durPnL >= 0 ? "var(--green)" : "var(--red)",
                  ],
                  ["Convexity P&L", daResult.convPnL, "var(--green)"],
                  [
                    "New Price",
                    da.P + daResult.durPnL + daResult.convPnL,
                    "var(--text-primary)",
                  ],
                ].map(([l, v, c]) => (
                  <div key={l}>
                    <div
                      style={{
                        fontSize: 9.5,
                        fontWeight: 600,
                        textTransform: "uppercase",
                        letterSpacing: "0.07em",
                        color: "var(--text-muted)",
                        marginBottom: 4,
                      }}
                    >
                      {l}
                    </div>
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 17,
                        fontWeight: 700,
                        color: c,
                      }}
                    >
                      {typeof v === "number"
                        ? (v >= 0 && l !== "New Price" ? "+" : "") +
                          v.toFixed(3)
                        : v}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-title" style={{ marginBottom: 12 }}>
              P&L vs Yield Shift
            </div>
            <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
              {[
                ["Duration Only", chartColors.amber],
                ["Dur+Convexity", chartColors.indigo],
              ].map(([l, c]) => (
                <div key={l} className="legend-item">
                  <div className="legend-dot" style={{ background: c }} />
                  <span>{l}</span>
                </div>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart
                data={daChartData}
                margin={{ top: 4, right: 10, bottom: 0, left: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(99,120,180,0.12)"
                />
                <XAxis
                  dataKey="shift"
                  tick={{
                    fill: "#4e6080",
                    fontSize: 10,
                    fontFamily: "var(--font-mono)",
                  }}
                  interval={4}
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
                  dataKey="Duration Only"
                  stroke={chartColors.amber}
                  strokeWidth={2}
                  strokeDasharray="5 3"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="Dur+Convexity"
                  stroke={chartColors.indigo}
                  strokeWidth={2.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Benchmark Spreads */}
      {tab === "spreads" && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              IG &amp; HY Benchmark Spreads — GET
              /api/v1/analytics/benchmark-spreads/
            </span>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
              10Y UST: 4.312%
            </span>
          </div>
          <ResponsiveContainer
            width="100%"
            height={200}
            style={{ marginBottom: 14 }}
          >
            <BarChart
              data={benchmarkSpreads}
              margin={{ top: 4, right: 10, bottom: 0, left: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(99,120,180,0.12)"
              />
              <XAxis
                dataKey="rating"
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
              <Bar dataKey="oas" name="OAS (bp)" radius={[3, 3, 0, 0]}>
                {benchmarkSpreads.map((_, i) => (
                  <Cell
                    key={i}
                    fill={i < 10 ? chartColors.indigo : chartColors.red}
                    fillOpacity={0.75}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rating</th>
                  <th>Category</th>
                  <th className="text-right">OAS (bp)</th>
                  <th className="text-right">YTM</th>
                  <th className="text-right">vs 10Y UST</th>
                  <th className="text-right">Sample</th>
                </tr>
              </thead>
              <tbody>
                {benchmarkSpreads.map((s, i) => (
                  <tr key={s.rating}>
                    <td>
                      <span className={`badge ${ratingBadge(s.rating)}`}>
                        {s.rating}
                      </span>
                    </td>
                    <td style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {i < 10 ? "Investment Grade" : "High Yield"}
                    </td>
                    <td
                      className="text-right mono"
                      style={{
                        color: i < 10 ? chartColors.indigo : chartColors.red,
                      }}
                    >
                      {s.oas}
                    </td>
                    <td className="text-right mono">{fmt.pct(s.ytm)}</td>
                    <td
                      className="text-right mono"
                      style={{ color: "var(--amber)" }}
                    >
                      +{((s.ytm - 0.04312) * 10000).toFixed(0)}bp
                    </td>
                    <td
                      className="text-right mono"
                      style={{ color: "var(--text-muted)", fontSize: 11 }}
                    >
                      {s.n}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Rolling Vol */}
      {tab === "vol" && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              Rolling 21-Day Annualised Volatility — 10Y UST
            </span>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
              POST /api/v1/analytics/rolling-volatility/
            </span>
          </div>
          <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
            {[
              [
                "Current",
                (volData.filter((d) => d.vol != null).at(-1)?.vol || 0).toFixed(
                  3,
                ) + "%",
                "var(--teal-400)",
              ],
              [
                "Max",
                Math.max(
                  ...volData.filter((d) => d.vol != null).map((d) => d.vol),
                ).toFixed(3) + "%",
                "var(--red)",
              ],
              [
                "Min",
                Math.min(
                  ...volData.filter((d) => d.vol != null).map((d) => d.vol),
                ).toFixed(3) + "%",
                "var(--green)",
              ],
            ].map(([l, v, c]) => (
              <div
                key={l}
                style={{
                  padding: "5px 12px",
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
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart
              data={volData}
              margin={{ top: 4, right: 10, bottom: 0, left: 0 }}
            >
              <defs>
                <linearGradient id="vg" x1="0" y1="0" x2="0" y2="1">
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
                interval={14}
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
                dataKey="vol"
                name="Vol (%)"
                stroke={chartColors.amber}
                strokeWidth={2}
                fill="url(#vg)"
                connectNulls
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Yield History */}
      {tab === "history" && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              US Treasury Yield History — GET /api/v1/analytics/yield-history/
            </span>
          </div>
          <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
            {[
              ["10Y", chartColors.indigo],
              ["5Y", chartColors.amber],
              ["2Y", chartColors.red],
            ].map(([l, c]) => (
              <div key={l} className="legend-item">
                <div className="legend-dot" style={{ background: c }} />
                <span>{l} UST</span>
              </div>
            ))}
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart
              data={histData}
              margin={{ top: 4, right: 10, bottom: 0, left: 0 }}
            >
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
                interval={18}
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
              <Line
                type="monotone"
                dataKey="10Y"
                stroke={chartColors.indigo}
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="5Y"
                stroke={chartColors.amber}
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="2Y"
                stroke={chartColors.red}
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3,1fr)",
              gap: 12,
              marginTop: 16,
            }}
          >
            {[
              ["10Y UST", history10y.rates, chartColors.indigo],
              ["5Y UST", history5y.rates, chartColors.amber],
              ["2Y UST", history2y.rates, chartColors.red],
            ].map(([l, r, c]) => {
              const last = r[r.length - 1],
                first = r[0],
                chg = last - first;
              return (
                <div
                  key={l}
                  style={{
                    background: "var(--bg-overlay)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--r-md)",
                    padding: 12,
                    textAlign: "center",
                  }}
                >
                  <div
                    style={{
                      fontSize: 10,
                      color: "var(--text-muted)",
                      fontWeight: 600,
                      marginBottom: 5,
                    }}
                  >
                    {l}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 22,
                      fontWeight: 700,
                      color: c,
                    }}
                  >
                    {(last * 100).toFixed(3)}%
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      fontFamily: "var(--font-mono)",
                      color: chg >= 0 ? "var(--red)" : "var(--green)",
                      marginTop: 3,
                    }}
                  >
                    {chg >= 0 ? "+" : ""}
                    {(chg * 100).toFixed(0)}bp (6M)
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}
