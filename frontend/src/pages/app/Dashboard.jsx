import { useState } from "react";
import { Link } from "react-router-dom";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Shield,
  Brain,
  BarChart3,
  Layers,
} from "lucide-react";
import {
  portfolios,
  treasury,
  history10y,
  history2y,
  mlForecast,
  scenarios,
  bonds,
  fmt,
  chartColors,
} from "../../data/mockData";

const CustomTooltip = ({ active, payload, label, pct }) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "#111927",
        border: "1px solid rgba(99,120,180,0.3)",
        borderRadius: 8,
        padding: "10px 13px",
        fontSize: 11,
      }}
    >
      <div
        style={{
          color: "#8898b8",
          marginBottom: 5,
          fontFamily: "var(--font-mono)",
        }}
      >
        {label}
      </div>
      {payload.map((p) => (
        <div
          key={p.name}
          style={{
            color: p.color,
            fontFamily: "var(--font-mono)",
            fontWeight: 600,
            marginBottom: 2,
          }}
        >
          {p.name}: {pct ? (p.value * 100).toFixed(3) + "%" : p.value}
        </div>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const totMV = portfolios.reduce((s, p) => s + p.mv, 0);
  const totPnL = portfolios.reduce((s, p) => s + p.pnl, 0);
  const avgYTM = portfolios.reduce((s, p) => s + p.ytm * p.mv, 0) / totMV;
  const avgDur = portfolios.reduce((s, p) => s + p.dur * p.mv, 0) / totMV;
  const totVar = portfolios.reduce((s, p) => s + p.var_99, 0);

  const curveData = treasury.points.map((p) => ({
    tenor: p.t + "Y",
    "Par Yield": +(p.y * 100).toFixed(3),
    "Spot Rate": treasury.spots[p.t + "Y"]
      ? +(treasury.spots[p.t + "Y"] * 100).toFixed(3)
      : null,
  }));

  const histData = history10y.labels.slice(-90).map((d, i) => ({
    date: d.slice(5),
    "10Y": +(history10y.rates.slice(-90)[i] * 100).toFixed(3),
    "2Y": +(history2y.rates.slice(-90)[i] * 100).toFixed(3),
  }));

  const fctData = mlForecast.labels.slice(0, 30).map((d, i) => ({
    date: d.slice(5),
    Point: +(mlForecast.point[i] * 100).toFixed(3),
    Upper: +(mlForecast.upper[i] * 100).toFixed(3),
    Lower: +(mlForecast.lower[i] * 100).toFixed(3),
  }));

  const sectorPie = Object.entries(portfolios[0].sector).map(
    ([name, value]) => ({ name, value: +(value * 100).toFixed(1) }),
  );
  const pieColors = [
    chartColors.indigo,
    chartColors.teal,
    chartColors.amber,
    chartColors.violet,
    chartColors.green,
  ];

  const KPIS = [
    {
      label: "Total AUM",
      value: fmt.moneyM(totMV),
      meta: "+2.14% MoM",
      up: true,
      icon: DollarSign,
      stripe: "indigo",
    },
    {
      label: "Avg YTM",
      value: fmt.pct(avgYTM),
      meta: "−12bp vs benchmark",
      up: false,
      icon: TrendingUp,
      stripe: "teal",
    },
    {
      label: "Unrealised P&L",
      value: fmt.moneyM(Math.abs(totPnL)),
      meta: fmt.signPct(totPnL / totMV),
      up: totPnL > 0,
      icon: Activity,
      stripe: totPnL > 0 ? "green" : "red",
    },
    {
      label: "Avg Duration",
      value: avgDur.toFixed(2) + "Y",
      meta: "Wtd Macaulay",
      up: null,
      icon: BarChart3,
      stripe: "amber",
    },
    {
      label: "VaR 99% (1d)",
      value: fmt.moneyM(totVar),
      meta: "Historical sim.",
      up: false,
      icon: Shield,
      stripe: "red",
    },
    {
      label: "Bonds Tracked",
      value: bonds.length.toString(),
      meta: `${portfolios.reduce((s, p) => s + p.positions.length, 0)} positions`,
      up: null,
      icon: Layers,
      stripe: "violet",
    },
    {
      label: "Curve Regime",
      value: "Inverted",
      meta: "2s10s −48bp · 87%",
      up: false,
      icon: TrendingDown,
      stripe: "red",
    },
    {
      label: "ML Backend",
      value: "Transformer",
      meta: `10Y target: ${fmt.pct(mlForecast.point[60])}`,
      up: null,
      icon: Brain,
      stripe: "indigo",
    },
  ];

  return (
    <>
      {/* KPI Grid */}
      <div className="kpi-grid mb-20">
        {KPIS.map((k) => (
          <div
            key={k.label}
            className={`kpi-card card-stripe card-stripe-${k.stripe}`}
          >
            <div className="kpi-card-label">{k.label}</div>
            <div
              className={`kpi-card-value ${k.value.length > 7 ? "sm" : ""}`}
              style={{
                color: k.value === "Inverted" ? "var(--red)" : undefined,
              }}
            >
              {k.value}
            </div>
            <div className="kpi-card-meta">
              {k.up !== null && (
                <span className={`kpi-delta ${k.up ? "up" : "down"}`}>
                  {k.meta}
                </span>
              )}
              {k.up === null && <span>{k.meta}</span>}
            </div>
            <k.icon className="kpi-icon" size={28} />
          </div>
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid-2-1 mb-20">
        <div className="card">
          <div className="card-header">
            <span className="card-title">US Treasury Yield Curve</span>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span className="regime-chip regime-inverted">⬇ Inverted</span>
              <Link to="/app/curves" className="card-action">
                Full Analysis →
              </Link>
            </div>
          </div>
          <div className="chart-legend">
            <div className="legend-item">
              <div
                className="legend-dot"
                style={{ background: chartColors.teal }}
              />
              <span>Par Yields</span>
            </div>
            <div className="legend-item">
              <div
                className="legend-dot"
                style={{
                  background: chartColors.indigo,
                  borderTop: "2px dashed",
                }}
              />
              <span>Spot Rates</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart
              data={curveData}
              margin={{ top: 4, right: 8, bottom: 0, left: 0 }}
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
                domain={["auto", "auto"]}
                tickFormatter={(v) => v + "%"}
              />
              <Tooltip content={<CustomTooltip pct={false} />} />
              <Line
                type="monotone"
                dataKey="Par Yield"
                stroke={chartColors.teal}
                strokeWidth={2.5}
                dot={{ r: 3, fill: chartColors.teal }}
              />
              <Line
                type="monotone"
                dataKey="Spot Rate"
                stroke={chartColors.indigo}
                strokeWidth={2}
                strokeDasharray="5 3"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Sector Exposure</span>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Core FI
            </span>
          </div>
          <ResponsiveContainer width="100%" height={150}>
            <PieChart>
              <Pie
                data={sectorPie}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={68}
                dataKey="value"
                paddingAngle={2}
              >
                {sectorPie.map((_, i) => (
                  <Cell key={i} fill={pieColors[i % pieColors.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(v) => v + "%"}
                contentStyle={{
                  background: "#111927",
                  border: "1px solid rgba(99,120,180,0.3)",
                  borderRadius: 8,
                  fontSize: 11,
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 7,
              marginTop: 4,
            }}
          >
            {sectorPie.map((s, i) => (
              <div key={s.name} className="alloc-row">
                <span className="alloc-label">{s.name}</span>
                <div className="alloc-track">
                  <div
                    className="alloc-fill"
                    style={{
                      width: `${s.value}%`,
                      background: pieColors[i % pieColors.length],
                    }}
                  />
                </div>
                <span className="alloc-pct">{s.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid-2 mb-20">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Rate History (90d)</span>
          </div>
          <div className="chart-legend">
            <div className="legend-item">
              <div
                className="legend-dot"
                style={{ background: chartColors.indigo }}
              />
              <span>10Y UST</span>
            </div>
            <div className="legend-item">
              <div
                className="legend-dot"
                style={{ background: chartColors.red }}
              />
              <span>2Y UST</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart
              data={histData}
              margin={{ top: 4, right: 8, bottom: 0, left: 0 }}
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
                interval={14}
              />
              <YAxis
                tick={{
                  fill: "#4e6080",
                  fontSize: 10,
                  fontFamily: "var(--font-mono)",
                }}
                domain={["auto", "auto"]}
                tickFormatter={(v) => v + "%"}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="10Y"
                stroke={chartColors.indigo}
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

        <div className="card">
          <div className="card-header">
            <span className="card-title">AI Rate Forecast (30d)</span>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              <span className="badge badge-indigo">Transformer</span>
              <span className="badge badge-teal">90% CI</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart
              data={fctData}
              margin={{ top: 4, right: 8, bottom: 0, left: 0 }}
            >
              <defs>
                <linearGradient id="fctGrad" x1="0" y1="0" x2="0" y2="1">
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
                interval={6}
              />
              <YAxis
                tick={{
                  fill: "#4e6080",
                  fontSize: 10,
                  fontFamily: "var(--font-mono)",
                }}
                domain={["auto", "auto"]}
                tickFormatter={(v) => v + "%"}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="Upper"
                stroke="transparent"
                fill={chartColors.indigo}
                fillOpacity={0.08}
              />
              <Area
                type="monotone"
                dataKey="Point"
                stroke={chartColors.indigo}
                strokeWidth={2}
                fill="url(#fctGrad)"
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
      </div>

      {/* Bottom row */}
      <div className="grid-2">
        {/* Portfolio summary */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Portfolio Overview</span>
            <Link to="/app/portfolios" className="card-action">
              Manage →
            </Link>
          </div>
          {portfolios.map((p) => (
            <div key={p.id} style={{ marginBottom: 14 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 4,
                }}
              >
                <span
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: "var(--text-primary)",
                  }}
                >
                  {p.name}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 12,
                    fontWeight: 600,
                    color: p.pnl >= 0 ? "var(--green)" : "var(--red)",
                  }}
                >
                  {fmt.signM(p.pnl)}
                </span>
              </div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: 5,
                }}
              >
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {fmt.moneyM(p.mv)}
                </span>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  Dur {p.dur.toFixed(2)}Y · YTM {fmt.pct(p.ytm)}
                </span>
              </div>
              <div className="progress">
                <div
                  className="progress-fill"
                  style={{
                    width: `${((p.mv / totMV) * 100).toFixed(0)}%`,
                    background: "var(--indigo-500)",
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Scenario heatmap */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Scenario P&L — Core FI</span>
            <Link to="/app/portfolios" className="card-action">
              All Scenarios →
            </Link>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Scenario</th>
                  <th className="text-right">P&L</th>
                  <th className="text-right">%</th>
                </tr>
              </thead>
              <tbody>
                {scenarios.slice(0, 7).map((s) => {
                  const pnl = s.p001,
                    pct = pnl / portfolios[0].mv;
                  return (
                    <tr key={s.name}>
                      <td style={{ fontSize: 12 }}>{s.name}</td>
                      <td
                        className="text-right mono"
                        style={{
                          color: pnl >= 0 ? "var(--green)" : "var(--red)",
                          fontSize: 12,
                        }}
                      >
                        {fmt.signM(pnl)}
                      </td>
                      <td
                        className="text-right mono"
                        style={{
                          color: pnl >= 0 ? "var(--green)" : "var(--red)",
                          fontSize: 11,
                        }}
                      >
                        {fmt.signPct(pct)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
