import { useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Plus, X, TrendingUp, TrendingDown } from "lucide-react";
import {
  portfolios,
  bonds,
  scenarios,
  fmt,
  ratingBadge,
  chartColors,
} from "../../data/mockData";
import { useToast } from "../../context/ToastContext";

const PIE_COLORS = [
  chartColors.indigo,
  chartColors.teal,
  chartColors.amber,
  chartColors.violet,
  chartColors.green,
  chartColors.red,
];

const ChartTip = ({ active, payload, label }) => {
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
          }}
        >
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
};

function VarModal({ portfolio, onClose }) {
  const toast = useToast();
  const [conf, setConf] = useState(99);
  const [hp, setHp] = useState(1);
  const [method, setMethod] = useState("historical");
  const [result, setResult] = useState(null);

  const run = () => {
    const var_est = portfolio.var_99 * (conf / 99) * Math.sqrt(hp);
    const cvar_est = var_est * 1.28;
    setResult({ var_est, cvar_est, pct: var_est / portfolio.mv });
    toast(
      "VaR computed · POST /api/v1/portfolios/" + portfolio.id + "/var/",
      "success",
    );
  };

  return (
    <div
      className="modal-backdrop"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="modal" style={{ maxWidth: 480 }}>
        <div className="modal-header">
          <span className="modal-title">
            VaR Configuration — {portfolio.name}
          </span>
          <button className="modal-close" onClick={onClose}>
            <X size={14} />
          </button>
        </div>
        <div className="modal-body">
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 12,
              marginBottom: 12,
            }}
          >
            <div className="form-group">
              <label className="form-label">Method</label>
              <select
                className="form-control"
                value={method}
                onChange={(e) => setMethod(e.target.value)}
              >
                <option value="historical">Historical</option>
                <option value="parametric">Parametric</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Confidence (%)</label>
              <input
                type="number"
                className="form-control"
                value={conf}
                min={90}
                max={99.99}
                step={0.01}
                onChange={(e) => setConf(+e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Holding Period (days)</label>
              <input
                type="number"
                className="form-control"
                value={hp}
                min={1}
                max={252}
                onChange={(e) => setHp(+e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Lookback (days)</label>
              <input
                type="number"
                className="form-control"
                defaultValue={252}
                min={21}
                max={2520}
              />
            </div>
          </div>
          <button className="btn btn-primary" onClick={run}>
            Run VaR
          </button>
          {result && (
            <div
              style={{
                marginTop: 16,
                background: "var(--bg-overlay)",
                border: "1px solid var(--border)",
                borderRadius: "var(--r-lg)",
                padding: 16,
              }}
            >
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr",
                  gap: 12,
                  textAlign: "center",
                }}
              >
                {[
                  [
                    "VaR " + conf + "%",
                    fmt.money(result.var_est),
                    "var(--red)",
                  ],
                  ["CVaR / ES", fmt.money(result.cvar_est), "var(--red)"],
                  [
                    "% of NAV",
                    (result.pct * 100).toFixed(2) + "%",
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
                        marginBottom: 5,
                      }}
                    >
                      {l}
                    </div>
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 20,
                        fontWeight: 700,
                        color: c,
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
      </div>
    </div>
  );
}

function CustomScenarioModal({ portfolio, onClose }) {
  const toast = useToast();
  const [f, setF] = useState({ parallel: 50, short: 25, long: -25, credit: 0 });
  const [result, setResult] = useState(null);
  const set = (k) => (e) => setF((p) => ({ ...p, [k]: +e.target.value }));

  const run = () => {
    const pnl =
      -portfolio.dv01 * f.parallel -
      portfolio.dv01 * 0.25 * (f.short + f.long) -
      portfolio.dv01 * 0.15 * f.credit;
    setResult(pnl);
    toast(
      "Scenario computed · POST /api/v1/portfolios/" +
        portfolio.id +
        "/custom-scenario/",
      "success",
    );
  };

  return (
    <div
      className="modal-backdrop"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="modal" style={{ maxWidth: 480 }}>
        <div className="modal-header">
          <span className="modal-title">
            Custom Scenario — {portfolio.name}
          </span>
          <button className="modal-close" onClick={onClose}>
            <X size={14} />
          </button>
        </div>
        <div className="modal-body">
          <div
            style={{
              fontSize: 12,
              color: "var(--text-muted)",
              marginBottom: 14,
            }}
          >
            All shifts in basis points. Uses DV01-based approximation.
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 12,
              marginBottom: 12,
            }}
          >
            {[
              ["Parallel Shift", "parallel"],
              ["Twist Short", "short"],
              ["Twist Long", "long"],
              ["Credit Spread", "credit"],
            ].map(([l, k]) => (
              <div key={k} className="form-group">
                <label className="form-label">{l} (bp)</label>
                <input
                  type="number"
                  className="form-control"
                  value={f[k]}
                  step={5}
                  onChange={set(k)}
                />
              </div>
            ))}
          </div>
          <button className="btn btn-primary" onClick={run}>
            Run Scenario
          </button>
          {result != null && (
            <div
              style={{
                marginTop: 14,
                background: "var(--bg-overlay)",
                border: "1px solid var(--border)",
                borderRadius: "var(--r-lg)",
                padding: 16,
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontSize: 10,
                  color: "var(--text-muted)",
                  marginBottom: 6,
                  textTransform: "uppercase",
                  letterSpacing: "0.07em",
                }}
              >
                Estimated P&L
              </div>
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 32,
                  fontWeight: 700,
                  color: result >= 0 ? "var(--green)" : "var(--red)",
                }}
              >
                {fmt.signM(result)}
              </div>
              <div
                style={{
                  fontSize: 11,
                  color: "var(--text-muted)",
                  marginTop: 4,
                }}
              >
                {fmt.signPct(result / portfolio.mv)} of NAV
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Portfolios() {
  const toast = useToast();
  const [selected, setSelected] = useState(portfolios[0]);
  const [varModal, setVarModal] = useState(false);
  const [scenModal, setScenModal] = useState(false);
  const [addModal, setAddModal] = useState(false);
  const totMV = portfolios.reduce((s, p) => s + p.mv, 0);

  const sectorData = Object.entries(selected.sector).map(([n, v]) => ({
    name: n,
    value: +(v * 100).toFixed(1),
  }));
  const ratingData = Object.entries(selected.rating).map(([n, v]) => ({
    name: n,
    value: +(v * 100).toFixed(1),
  }));
  const matData = Object.entries(selected.maturity).map(([n, v]) => ({
    name: n,
    value: +(v * 100).toFixed(1),
  }));
  const scenData = scenarios.map((s) => ({
    name: s.name.slice(0, 18),
    pnl: s["p" + selected.id.slice(1)],
  }));

  return (
    <>
      {/* Portfolio cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3,1fr)",
          gap: 14,
          marginBottom: 20,
        }}
      >
        {portfolios.map((p) => (
          <div
            key={p.id}
            className={`card card-stripe card-stripe-${p.pnl >= 0 ? "teal" : "red"}`}
            style={{
              cursor: "pointer",
              transition: "all 0.18s",
              borderColor:
                selected?.id === p.id ? "var(--indigo-500)" : undefined,
              boxShadow:
                selected?.id === p.id ? "var(--shadow-glow-indigo)" : undefined,
            }}
            onClick={() => setSelected(p)}
          >
            <div className="card-header">
              <span
                style={{
                  fontFamily: "var(--font-head)",
                  fontSize: 13.5,
                  fontWeight: 700,
                }}
              >
                {p.name}
              </span>
              <span className="badge badge-gray">{p.currency}</span>
            </div>
            <div
              style={{
                fontSize: 11.5,
                color: "var(--text-muted)",
                marginBottom: 12,
              }}
            >
              {p.desc}
            </div>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 24,
                fontWeight: 700,
                marginBottom: 12,
              }}
            >
              {fmt.moneyM(p.mv)}
            </div>
            <div className="metric-strip" style={{ marginBottom: 10 }}>
              <div className="metric-cell">
                <div className="metric-cell-label">Duration</div>
                <div className="metric-cell-value" style={{ fontSize: 14 }}>
                  {p.dur.toFixed(2)}
                </div>
              </div>
              <div className="metric-cell">
                <div className="metric-cell-label">YTM</div>
                <div
                  className="metric-cell-value"
                  style={{ fontSize: 14, color: "var(--teal-400)" }}
                >
                  {fmt.pct(p.ytm)}
                </div>
              </div>
              <div className="metric-cell">
                <div className="metric-cell-label">DV01</div>
                <div className="metric-cell-value" style={{ fontSize: 14 }}>
                  {(p.dv01 / 1000).toFixed(1)}K
                </div>
              </div>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                paddingTop: 10,
                borderTop: "1px solid var(--border)",
              }}
            >
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                Unrealised P&L
              </span>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  fontWeight: 600,
                  color: p.pnl >= 0 ? "var(--green)" : "var(--red)",
                }}
              >
                {fmt.signM(p.pnl)} ({fmt.signPct(p.pnl_pct)})
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginTop: 6,
              }}
            >
              <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                VaR 99% 1d
              </span>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  color: "var(--red)",
                }}
              >
                {fmt.money(p.var_99)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Detail header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 16,
        }}
      >
        <h2
          style={{
            fontFamily: "var(--font-head)",
            fontSize: 17,
            fontWeight: 700,
          }}
        >
          {selected.name}
        </h2>
        <span className="badge badge-gray">{selected.currency}</span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setVarModal(true)}
          >
            VaR Config
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setScenModal(true)}
          >
            Custom Scenario
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={() =>
              toast(
                "POST /api/v1/portfolios/" + selected.id + "/positions/",
                "info",
              )
            }
          >
            <Plus size={13} /> Position
          </button>
        </div>
      </div>

      {/* Key metrics */}
      <div className="metric-strip mb-16">
        {[
          ["Market Value", fmt.moneyM(selected.mv)],
          ["Face Value", fmt.moneyM(selected.fv)],
          ["Duration", selected.dur.toFixed(2) + "Y"],
          ["Mod. Dur.", selected.mdur.toFixed(2) + "Y"],
          ["Convexity", selected.conv.toFixed(1)],
          ["YTM", fmt.pct(selected.ytm), "var(--teal-400)"],
          ["DV01", selected.dv01.toFixed(0), "var(--amber)"],
          ["Positions", selected.positions.length.toString()],
        ].map(([l, v, c]) => (
          <div key={l} className="metric-cell">
            <div className="metric-cell-label">{l}</div>
            <div
              className="metric-cell-value"
              style={{ color: c, fontSize: 14 }}
            >
              {v}
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: 16,
          marginBottom: 16,
        }}
      >
        {/* Sector */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>
            Sector Allocation
          </div>
          <ResponsiveContainer width="100%" height={130}>
            <PieChart>
              <Pie
                data={sectorData}
                cx="50%"
                cy="50%"
                innerRadius={38}
                outerRadius={56}
                dataKey="value"
                paddingAngle={2}
              >
                {sectorData.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
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
          {sectorData.map((s, i) => (
            <div key={s.name} className="alloc-row">
              <span className="alloc-label" style={{ fontSize: 11 }}>
                {s.name}
              </span>
              <div className="alloc-track">
                <div
                  className="alloc-fill"
                  style={{
                    width: s.value + "%",
                    background: PIE_COLORS[i % PIE_COLORS.length],
                  }}
                />
              </div>
              <span className="alloc-pct">{s.value}%</span>
            </div>
          ))}
        </div>
        {/* Rating */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>
            Rating Distribution
          </div>
          <ResponsiveContainer width="100%" height={130}>
            <PieChart>
              <Pie
                data={ratingData}
                cx="50%"
                cy="50%"
                innerRadius={38}
                outerRadius={56}
                dataKey="value"
                paddingAngle={2}
              >
                {ratingData.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
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
          {ratingData.map((s, i) => (
            <div key={s.name} className="alloc-row">
              <span className="alloc-label" style={{ fontSize: 11 }}>
                {s.name}
              </span>
              <div className="alloc-track">
                <div
                  className="alloc-fill"
                  style={{
                    width: s.value + "%",
                    background: PIE_COLORS[i % PIE_COLORS.length],
                  }}
                />
              </div>
              <span className="alloc-pct">{s.value}%</span>
            </div>
          ))}
        </div>
        {/* VaR / Risk */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>
            Risk Metrics
          </div>
          <div style={{ textAlign: "center", padding: "10px 0 14px" }}>
            <div
              style={{
                fontSize: 10,
                color: "var(--text-muted)",
                marginBottom: 5,
              }}
            >
              VaR 99% (1-Day Historical)
            </div>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 32,
                fontWeight: 700,
                color: "var(--red)",
              }}
            >
              {fmt.money(selected.var_99)}
            </div>
            <div
              style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 3 }}
            >
              CVaR: {fmt.money(selected.cvar_99)}
            </div>
          </div>
          <div className="divider" />
          <div className="stat-list">
            {[
              ["VaR 95% (1d)", fmt.money(selected.var_95)],
              [
                "Unrealised P&L",
                fmt.signM(selected.pnl),
                selected.pnl >= 0 ? "pos" : "neg",
              ],
              [
                "P&L %",
                fmt.signPct(selected.pnl_pct),
                selected.pnl >= 0 ? "pos" : "neg",
              ],
            ].map(([k, v, c]) => (
              <div key={k} className="stat-row">
                <span className="stat-key">{k}</span>
                <span className={`stat-val ${c || ""}`}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Positions table */}
      <div className="card mb-16" style={{ padding: 0 }}>
        <div
          style={{
            padding: "14px 20px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span className="card-title">
            Positions ({selected.positions.length})
          </span>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Bond</th>
                <th>Rating</th>
                <th className="text-right">Face Amount</th>
                <th className="text-right">Mkt Value</th>
                <th className="text-right">Weight</th>
                <th className="text-right">YTM</th>
                <th className="text-right">Duration</th>
                <th className="text-right">Purchase Px</th>
              </tr>
            </thead>
            <tbody>
              {selected.positions.map((pos) => {
                const bond = bonds.find((b) => b.id === pos.bond_id);
                if (!bond) return null;
                const mv = (bond.dirty_price / 100) * pos.face;
                const wt = mv / selected.mv;
                return (
                  <tr key={pos.bond_id}>
                    <td>
                      <div style={{ fontWeight: 600, fontSize: 12.5 }}>
                        {bond.issuer}
                      </div>
                      <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
                        {(bond.coupon_rate * 100).toFixed(2)}%{" "}
                        {bond.maturity_date.slice(0, 7)}
                      </div>
                    </td>
                    <td>
                      <span
                        className={`badge ${ratingBadge(bond.credit_rating)}`}
                      >
                        {bond.credit_rating || "—"}
                      </span>
                    </td>
                    <td className="text-right mono">
                      {(pos.face / 1e6).toFixed(2)}M
                    </td>
                    <td className="text-right mono">
                      {(mv / 1e6).toFixed(2)}M
                    </td>
                    <td className="text-right mono">
                      {(wt * 100).toFixed(1)}%
                    </td>
                    <td
                      className="text-right mono"
                      style={{ color: "var(--teal-400)" }}
                    >
                      {fmt.pct(bond.ytm)}
                    </td>
                    <td className="text-right mono">
                      {bond.duration.toFixed(2)}
                    </td>
                    <td
                      className="text-right mono"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {pos.px.toFixed(3)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Scenarios */}
      <div className="card mb-16">
        <div className="card-header">
          <span className="card-title">
            Standard Rate Scenarios — 10 Shocks
          </span>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setScenModal(true)}
          >
            Custom →
          </button>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Scenario</th>
                <th className="text-right">Est. P&L</th>
                <th className="text-right">P&L %</th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((s) => {
                const pnl = s["p" + selected.id.slice(1)];
                const pct = pnl / selected.mv;
                return (
                  <tr key={s.name}>
                    <td style={{ fontSize: 12 }}>{s.name}</td>
                    <td
                      className="text-right mono"
                      style={{
                        color: pnl >= 0 ? "var(--green)" : "var(--red)",
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

      {/* Maturity distribution */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: 14 }}>
          Maturity Distribution
        </div>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart
            data={matData}
            margin={{ top: 4, right: 8, bottom: 0, left: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(99,120,180,0.12)"
            />
            <XAxis
              dataKey="name"
              tick={{
                fill: "#4e6080",
                fontSize: 11,
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
            <Tooltip content={<ChartTip />} />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {matData.map((_, i) => (
                <Cell
                  key={i}
                  fill={PIE_COLORS[i % PIE_COLORS.length]}
                  fillOpacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {varModal && (
        <VarModal portfolio={selected} onClose={() => setVarModal(false)} />
      )}
      {scenModal && (
        <CustomScenarioModal
          portfolio={selected}
          onClose={() => setScenModal(false)}
        />
      )}
    </>
  );
}
