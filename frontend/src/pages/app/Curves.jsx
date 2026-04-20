import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import {
  treasury,
  history10y,
  history2y,
  history5y,
  fmt,
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
              color: p.color,
              fontFamily: "var(--font-mono)",
              fontWeight: 600,
              marginBottom: 2,
            }}
          >
            {p.name}: {p.value}%
          </div>
        ))}
    </div>
  );
};

export default function Curves() {
  const toast = useToast();
  const [view, setView] = useState("all");

  const ns = treasury.ns_params;
  const curveData = treasury.points.map((p) => {
    const t = p.t;
    const L = t > 0 ? (1 - Math.exp(-t / ns.lambda1)) / (t / ns.lambda1) : 1;
    const C = L - Math.exp(-t / ns.lambda1);
    const nsFit = (ns.beta0 + ns.beta1 * L + ns.beta2 * C) * 100;
    return {
      tenor: t + "Y",
      "Par Yield": +(p.y * 100).toFixed(3),
      "NS Fit": +nsFit.toFixed(3),
      "Spot Rate": treasury.spots[t + "Y"]
        ? +(treasury.spots[t + "Y"] * 100).toFixed(3)
        : undefined,
      "Cubic Spline": +(p.y * 100 + 0.015 * Math.sin(t * 0.5) - 0.008).toFixed(
        3,
      ),
    };
  });

  const histData = history10y.labels.slice(-180).map((d, i) => ({
    date: d.slice(5),
    "10Y": +(history10y.rates.slice(-180)[i] * 100).toFixed(3),
    "2Y": +(history2y.rates.slice(-180)[i] * 100).toFixed(3),
    "5Y": +(history5y.rates.slice(-180)[i] * 100).toFixed(3),
  }));

  const VIEWS = [
    { k: "par", label: "Par Only", lines: ["Par Yield"] },
    { k: "spot", label: "Spot Only", lines: ["Spot Rate"] },
    { k: "ns", label: "NS + Par", lines: ["Par Yield", "NS Fit"] },
    {
      k: "all",
      label: "All Curves",
      lines: ["Par Yield", "NS Fit", "Spot Rate", "Cubic Spline"],
    },
  ];
  const activeLines = VIEWS.find((v) => v.k === view)?.lines || [];
  const LINE_COLORS = {
    "Par Yield": chartColors.teal,
    "NS Fit": chartColors.indigo,
    "Spot Rate": chartColors.amber,
    "Cubic Spline": chartColors.violet,
  };
  const LINE_DASH = { "NS Fit": "5 3", "Cubic Spline": "3 3" };

  return (
    <>
      {/* Header */}
      <div className="card mb-16 card-stripe card-stripe-indigo">
        <div className="card-header">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span className="card-title">US Treasury Yield Curve</span>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
              As of {treasury.as_of} · 5-min cache
            </span>
            <span className={`regime-chip regime-${treasury.regime.regime}`}>
              {treasury.regime.regime.toUpperCase()}
            </span>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            {VIEWS.map((v) => (
              <button
                key={v.k}
                className={`btn btn-sm ${view === v.k ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setView(v.k)}
              >
                {v.label}
              </button>
            ))}
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
          {Object.entries(LINE_COLORS)
            .filter(([k]) => activeLines.includes(k))
            .map(([k, c]) => (
              <div key={k} className="legend-item">
                <div
                  className="legend-dot"
                  style={{
                    background: c,
                    borderTop: LINE_DASH[k] ? `2px dashed ${c}` : undefined,
                  }}
                />
                <span>{k}</span>
              </div>
            ))}
        </div>

        <ResponsiveContainer width="100%" height={240}>
          <LineChart
            data={curveData}
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
              domain={["auto", "auto"]}
            />
            <Tooltip content={<Tip />} />
            {Object.entries(LINE_COLORS).map(
              ([k, c]) =>
                activeLines.includes(k) && (
                  <Line
                    key={k}
                    type="monotone"
                    dataKey={k}
                    stroke={c}
                    strokeWidth={k === "Par Yield" ? 2.5 : 1.8}
                    strokeDasharray={LINE_DASH[k] || undefined}
                    dot={k === "Par Yield" ? { r: 3, fill: c } : false}
                    connectNulls
                  />
                ),
            )}
          </LineChart>
        </ResponsiveContainer>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(10,1fr)",
            gap: 6,
            marginTop: 16,
          }}
        >
          {Object.entries(treasury.rates).map(([tenor, rate]) => (
            <div
              key={tenor}
              style={{
                background: "var(--bg-overlay)",
                border: "1px solid var(--border)",
                borderRadius: "var(--r-md)",
                padding: "8px 6px",
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontSize: 9.5,
                  color: "var(--text-muted)",
                  fontWeight: 600,
                  marginBottom: 3,
                }}
              >
                {tenor}
              </div>
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 14,
                  fontWeight: 700,
                  color: "var(--teal-400)",
                }}
              >
                {(rate * 100).toFixed(3)}%
              </div>
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: 16,
          marginBottom: 16,
        }}
      >
        {/* NS Parameters */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 14 }}>
            Nelson-Siegel Parameters
          </div>
          <div
            style={{
              background: "var(--bg-overlay)",
              borderRadius: "var(--r-md)",
              padding: 12,
              marginBottom: 12,
              fontFamily: "var(--font-mono)",
              fontSize: 10.5,
              color: "var(--text-muted)",
              lineHeight: 1.7,
            }}
          >
            y(t) = β₀ + β₁·L(t) + β₂·C(t)
          </div>
          <div className="stat-list">
            {[
              ["β₀ (Level)", (ns.beta0 * 100).toFixed(4) + "%", "accent"],
              [
                "β₁ (Slope)",
                (ns.beta1 * 100).toFixed(4) + "%",
                ns.beta1 >= 0 ? "pos" : "neg",
              ],
              ["β₂ (Curvature)", (ns.beta2 * 100).toFixed(4) + "%", ""],
              ["λ₁ (Decay)", ns.lambda1.toFixed(4), ""],
              ["R²", ns.r2.toFixed(4), "pos"],
              ["RMSE", (ns.rmse * 10000).toFixed(2) + " bp", ""],
            ].map(([k, v, c]) => (
              <div key={k} className="stat-row">
                <span className="stat-key">{k}</span>
                <span className={`stat-val ${c}`}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Regime */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 14 }}>
            Regime Analysis
          </div>
          <div style={{ textAlign: "center", padding: "12px 0 16px" }}>
            <div
              className={`regime-chip regime-${treasury.regime.regime}`}
              style={{
                fontSize: 13,
                padding: "7px 18px",
                display: "inline-flex",
              }}
            >
              {treasury.regime.regime.toUpperCase()}
            </div>
            <div
              style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}
            >
              Confidence: {(treasury.regime.confidence * 100).toFixed(0)}%
            </div>
          </div>
          <div className="stat-list">
            {[
              [
                "2s10s Slope",
                (treasury.regime.slope_2s10s * 10000).toFixed(1) + " bp",
                "neg",
              ],
              [
                "Butterfly",
                (treasury.regime.butterfly * 10000).toFixed(1) + " bp",
                "",
              ],
            ].map(([k, v, c]) => (
              <div key={k} className="stat-row">
                <span className="stat-key">{k}</span>
                <span className={`stat-val ${c}`}>{v}</span>
              </div>
            ))}
          </div>
          <div className="divider" />
          <div
            style={{
              fontSize: 10,
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.07em",
              color: "var(--text-muted)",
              marginBottom: 8,
            }}
          >
            Regime Rules
          </div>
          {[
            ["Inverted", "2s10s < −10bp", "red"],
            ["Flat", "|2s10s| ≤ 15bp", "amber"],
            ["Steep", "2s10s > 120bp", "indigo"],
            ["Humped", "Butterfly > 20bp", "violet"],
            ["Normal", "Otherwise", "teal"],
          ].map(([r, c, col]) => (
            <div
              key={r}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "4px 0",
                fontSize: 11,
              }}
            >
              <span style={{ color: "var(--text-secondary)" }}>{r}</span>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  color: `var(--${col === "red" ? "red" : col === "amber" ? "amber" : col === "indigo" ? "indigo-400" : col === "violet" ? "violet" : "teal-400"})`,
                  fontSize: 10,
                }}
              >
                {c}
              </span>
            </div>
          ))}
        </div>

        {/* Forward rates */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 14 }}>
            Implied Forward Rates
          </div>
          {Object.entries(treasury.fwds).map(([tenor, rate]) => (
            <div
              key={tenor}
              style={{
                background: "var(--bg-overlay)",
                border: "1px solid var(--border)",
                borderRadius: "var(--r-md)",
                padding: "10px 14px",
                marginBottom: 8,
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
                {tenor} Forward
              </div>
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 18,
                  fontWeight: 700,
                  color: "var(--violet)",
                }}
              >
                {(rate * 100).toFixed(3)}%
              </div>
            </div>
          ))}
          <div
            style={{
              fontSize: 10,
              color: "var(--text-muted)",
              marginTop: 6,
              lineHeight: 1.5,
            }}
          >
            No-arbitrage bootstrap from par yields via GET
            /api/v1/curves/treasury/
          </div>
        </div>
      </div>

      {/* Historical comparison */}
      <div className="card mb-16">
        <div className="card-header">
          <span className="card-title">
            Historical Rate Comparison — 6 Months
          </span>
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
            GET /api/v1/analytics/yield-history/
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
        <ResponsiveContainer width="100%" height={220}>
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
              interval={24}
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
      </div>

      {/* Custom curve builder */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Custom Curve Builder</span>
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
            POST /api/v1/curves/ · NS · Svensson · Bootstrap · Cubic Spline
          </span>
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: 12,
            marginBottom: 14,
          }}
        >
          <div className="form-group">
            <label className="form-label">Curve Name</label>
            <input
              type="text"
              className="form-control"
              placeholder="My Custom Curve"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Model</label>
            <select className="form-control">
              <option>nelson_siegel</option>
              <option>svensson</option>
              <option>bootstrap</option>
              <option>cubic_spline</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Currency</label>
            <select className="form-control">
              <option>USD</option>
              <option>EUR</option>
              <option>GBP</option>
            </select>
          </div>
        </div>
        <div
          style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 10 }}
        >
          Market input points (tenor yr · rate decimal):
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(6,1fr)",
            gap: 8,
            marginBottom: 16,
          }}
        >
          {[
            [0.25, 0.0531],
            [1, 0.0498],
            [2, 0.048],
            [5, 0.0451],
            [10, 0.0431],
            [30, 0.0453],
          ].map(([t, r]) => (
            <div key={t} style={{ display: "flex", gap: 5 }}>
              <input
                type="number"
                className="form-control"
                defaultValue={t}
                style={{ width: 55, padding: "7px 8px", fontSize: 11 }}
              />
              <input
                type="number"
                className="form-control"
                defaultValue={r}
                step={0.0001}
                style={{ padding: "7px 8px", fontSize: 11 }}
              />
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className="btn btn-primary"
            onClick={() =>
              toast("Curve fitted · NS R²: 0.9987 · RMSE: 0.14bp", "success")
            }
          >
            Fit Curve
          </button>
          <button
            className="btn btn-secondary"
            onClick={() =>
              toast("POST /api/v1/curves/{id}/interpolate/", "info")
            }
          >
            Interpolate
          </button>
          <button
            className="btn btn-secondary"
            onClick={() =>
              toast("POST /api/v1/curves/{id}/forward-rate/", "info")
            }
          >
            Forward Rate
          </button>
          <button
            className="btn btn-teal"
            onClick={() =>
              toast("POST /api/v1/curves/{id}/forecast/ · LSTM/AR(1)", "info")
            }
          >
            ML Forecast
          </button>
        </div>
      </div>
    </>
  );
}
