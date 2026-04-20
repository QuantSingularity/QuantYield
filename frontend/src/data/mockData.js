// QuantYield — Mock Data (matches Django REST API schemas exactly)

export const bonds = [
  {
    id: "b001",
    name: "US Treasury 4.5% 2034",
    issuer: "US Treasury",
    isin: "US912810TM07",
    face_value: 1000,
    coupon_rate: 0.045,
    maturity_date: "2034-02-15",
    issue_date: "2024-02-15",
    coupon_frequency: "semiannual",
    bond_type: "fixed",
    day_count: "actual/actual",
    currency: "USD",
    credit_rating: "AAA",
    sector: "Government",
    dirty_price: 98.234,
    clean_price: 97.891,
    ytm: 0.04621,
    duration: 8.12,
    modified_duration: 7.94,
    convexity: 72.3,
    dv01: 793.4,
    accrued_interest: 0.343,
    years_to_maturity: 9.87,
  },
  {
    id: "b002",
    name: "Apple Inc 3.85% 2043",
    issuer: "Apple Inc",
    isin: "US037833AJ98",
    face_value: 1000,
    coupon_rate: 0.0385,
    maturity_date: "2043-05-04",
    issue_date: "2023-05-04",
    coupon_frequency: "semiannual",
    bond_type: "fixed",
    day_count: "30/360",
    currency: "USD",
    credit_rating: "AA+",
    sector: "Technology",
    dirty_price: 84.102,
    clean_price: 83.688,
    ytm: 0.05012,
    duration: 14.21,
    modified_duration: 13.86,
    convexity: 246.1,
    dv01: 1164.2,
    accrued_interest: 0.414,
    years_to_maturity: 18.29,
  },
  {
    id: "b003",
    name: "JPMorgan Chase 5.1% 2028",
    issuer: "JPMorgan Chase",
    isin: "US46647PAB72",
    face_value: 1000,
    coupon_rate: 0.051,
    maturity_date: "2028-04-11",
    issue_date: "2023-04-11",
    coupon_frequency: "semiannual",
    bond_type: "fixed",
    day_count: "30/360",
    currency: "USD",
    credit_rating: "A-",
    sector: "Financials",
    dirty_price: 99.758,
    clean_price: 99.401,
    ytm: 0.05145,
    duration: 4.23,
    modified_duration: 4.12,
    convexity: 19.7,
    dv01: 409.4,
    accrued_interest: 0.357,
    years_to_maturity: 4.06,
  },
  {
    id: "b004",
    name: "Amazon.com 4.95% 2052",
    issuer: "Amazon.com",
    isin: "US023135CK89",
    face_value: 1000,
    coupon_rate: 0.0495,
    maturity_date: "2052-12-05",
    issue_date: "2022-12-05",
    coupon_frequency: "semiannual",
    bond_type: "fixed",
    day_count: "30/360",
    currency: "USD",
    credit_rating: "AA",
    sector: "Technology",
    dirty_price: 88.521,
    clean_price: 87.982,
    ytm: 0.05651,
    duration: 19.84,
    modified_duration: 19.24,
    convexity: 476.3,
    dv01: 1692.5,
    accrued_interest: 0.539,
    years_to_maturity: 28.13,
  },
  {
    id: "b005",
    name: "Ford Motor 4.75% 2043",
    issuer: "Ford Motor Co",
    isin: "US345370DG54",
    face_value: 1000,
    coupon_rate: 0.0475,
    maturity_date: "2043-01-15",
    issue_date: "2023-01-15",
    coupon_frequency: "semiannual",
    bond_type: "callable",
    day_count: "30/360",
    currency: "USD",
    credit_rating: "BB+",
    sector: "Consumer Disc.",
    dirty_price: 79.431,
    clean_price: 79.058,
    ytm: 0.06512,
    duration: 13.44,
    modified_duration: 12.97,
    convexity: 223.4,
    dv01: 1028.2,
    accrued_interest: 0.373,
    years_to_maturity: 18.83,
  },
  {
    id: "b006",
    name: "Exxon Mobil 3.0% 2027",
    issuer: "Exxon Mobil",
    isin: "US30231GAV08",
    face_value: 1000,
    coupon_rate: 0.03,
    maturity_date: "2027-08-16",
    issue_date: "2022-08-16",
    coupon_frequency: "semiannual",
    bond_type: "fixed",
    day_count: "actual/actual",
    currency: "USD",
    credit_rating: "AA-",
    sector: "Energy",
    dirty_price: 95.234,
    clean_price: 94.912,
    ytm: 0.04698,
    duration: 3.31,
    modified_duration: 3.24,
    convexity: 12.1,
    dv01: 307.2,
    accrued_interest: 0.322,
    years_to_maturity: 3.33,
  },
  {
    id: "b007",
    name: "Microsoft 2.675% 2060",
    issuer: "Microsoft Corp",
    isin: "US594918BW61",
    face_value: 1000,
    coupon_rate: 0.02675,
    maturity_date: "2060-06-01",
    issue_date: "2020-06-01",
    coupon_frequency: "semiannual",
    bond_type: "fixed",
    day_count: "30/360",
    currency: "USD",
    credit_rating: "AAA",
    sector: "Technology",
    dirty_price: 54.712,
    clean_price: 54.428,
    ytm: 0.05412,
    duration: 24.83,
    modified_duration: 24.19,
    convexity: 712.8,
    dv01: 1323.4,
    accrued_interest: 0.284,
    years_to_maturity: 36.12,
  },
  {
    id: "b008",
    name: "US Treasury 5.0% 2026",
    issuer: "US Treasury",
    isin: "US91282CHN92",
    face_value: 1000,
    coupon_rate: 0.05,
    maturity_date: "2026-04-30",
    issue_date: "2024-04-30",
    coupon_frequency: "semiannual",
    bond_type: "fixed",
    day_count: "actual/actual",
    currency: "USD",
    credit_rating: "AAA",
    sector: "Government",
    dirty_price: 100.521,
    clean_price: 100.283,
    ytm: 0.04812,
    duration: 1.91,
    modified_duration: 1.88,
    convexity: 4.2,
    dv01: 187.4,
    accrued_interest: 0.238,
    years_to_maturity: 1.95,
  },
  {
    id: "b009",
    name: "Goldman Sachs 6.0% 2033",
    issuer: "Goldman Sachs",
    isin: "US38141GYF29",
    face_value: 1000,
    coupon_rate: 0.06,
    maturity_date: "2033-11-01",
    issue_date: "2023-11-01",
    coupon_frequency: "semiannual",
    bond_type: "fixed",
    day_count: "30/360",
    currency: "USD",
    credit_rating: "A+",
    sector: "Financials",
    dirty_price: 106.431,
    clean_price: 105.882,
    ytm: 0.05341,
    duration: 7.52,
    modified_duration: 7.31,
    convexity: 64.4,
    dv01: 776.2,
    accrued_interest: 0.549,
    years_to_maturity: 9.54,
  },
  {
    id: "b010",
    name: "Tesla Inc 5.3% 2025",
    issuer: "Tesla Inc",
    isin: "US88160RAP14",
    face_value: 1000,
    coupon_rate: 0.053,
    maturity_date: "2025-08-15",
    issue_date: "2020-08-15",
    coupon_frequency: "semiannual",
    bond_type: "callable",
    day_count: "30/360",
    currency: "USD",
    credit_rating: "B+",
    sector: "Consumer Disc.",
    dirty_price: 101.234,
    clean_price: 100.982,
    ytm: 0.04921,
    duration: 0.87,
    modified_duration: 0.86,
    convexity: 0.9,
    dv01: 85.6,
    accrued_interest: 0.252,
    years_to_maturity: 0.33,
  },
  {
    id: "b011",
    name: "Verizon Comm 4.4% 2034",
    issuer: "Verizon",
    isin: "US92343VGC12",
    face_value: 1000,
    coupon_rate: 0.044,
    maturity_date: "2034-11-01",
    issue_date: "2024-11-01",
    coupon_frequency: "semiannual",
    bond_type: "fixed",
    day_count: "30/360",
    currency: "USD",
    credit_rating: "BBB+",
    sector: "Telecom",
    dirty_price: 93.784,
    clean_price: 93.42,
    ytm: 0.04931,
    duration: 8.34,
    modified_duration: 8.11,
    convexity: 79.2,
    dv01: 758.4,
    accrued_interest: 0.364,
    years_to_maturity: 9.54,
  },
  {
    id: "b012",
    name: "US Treasury TIPS 2.375% 2029",
    issuer: "US Treasury",
    isin: "US912810PT55",
    face_value: 1000,
    coupon_rate: 0.02375,
    maturity_date: "2029-01-15",
    issue_date: "2024-01-15",
    coupon_frequency: "semiannual",
    bond_type: "inflation_linked",
    day_count: "actual/actual",
    currency: "USD",
    credit_rating: "AAA",
    sector: "Government",
    dirty_price: 96.124,
    clean_price: 95.842,
    ytm: 0.02981,
    duration: 4.62,
    modified_duration: 4.49,
    convexity: 23.8,
    dv01: 431.2,
    accrued_interest: 0.282,
    years_to_maturity: 4.83,
  },
];

export const portfolios = [
  {
    id: "p001",
    name: "Core Fixed Income",
    desc: "Investment grade government and corporate bonds",
    currency: "USD",
    positions: [
      { bond_id: "b001", face: 5000000, px: 99.124 },
      { bond_id: "b002", face: 2000000, px: 88.234 },
      { bond_id: "b006", face: 3000000, px: 97.215 },
      { bond_id: "b008", face: 8000000, px: 99.874 },
      { bond_id: "b012", face: 2500000, px: 97.332 },
    ],
    mv: 21284512,
    fv: 20500000,
    dur: 5.84,
    mdur: 5.71,
    conv: 52.3,
    ytm: 0.04821,
    dv01: 12148,
    sector: {
      Government: 0.62,
      Technology: 0.13,
      Energy: 0.13,
      "Infl. Linked": 0.12,
    },
    rating: { AAA: 0.76, "AA+": 0.13, "AA-": 0.11 },
    maturity: { "0–2Y": 0.39, "2–5Y": 0.11, "5–10Y": 0.34, "10Y+": 0.16 },
    var_99: 142334,
    cvar_99: 183221,
    var_95: 94812,
    pnl: 784512,
    pnl_pct: 0.0384,
  },
  {
    id: "p002",
    name: "High Yield Opportunities",
    desc: "BB/B rated corporate bonds for yield enhancement",
    currency: "USD",
    positions: [
      { bond_id: "b005", face: 3000000, px: 82.012 },
      { bond_id: "b010", face: 1500000, px: 100.432 },
      { bond_id: "b009", face: 2000000, px: 102.134 },
    ],
    mv: 7421812,
    fv: 6500000,
    dur: 8.24,
    mdur: 7.98,
    conv: 112.4,
    ytm: 0.05892,
    dv01: 5924,
    sector: { "Consumer Disc.": 0.62, Financials: 0.38 },
    rating: { "A+": 0.27, "BB+": 0.53, "B+": 0.2 },
    maturity: { "0–2Y": 0.2, "5–10Y": 0.27, "10Y+": 0.53 },
    var_99: 89124,
    cvar_99: 114832,
    var_95: 62341,
    pnl: 921812,
    pnl_pct: 0.0892,
  },
  {
    id: "p003",
    name: "Duration Overlay",
    desc: "Long duration government bonds for duration management",
    currency: "USD",
    positions: [
      { bond_id: "b007", face: 2000000, px: 57.124 },
      { bond_id: "b004", face: 3000000, px: 91.432 },
    ],
    mv: 4014248,
    fv: 5000000,
    dur: 21.92,
    mdur: 21.23,
    conv: 583.2,
    ytm: 0.05572,
    dv01: 8524,
    sector: { Technology: 1.0 },
    rating: { AAA: 0.34, AA: 0.66 },
    maturity: { "10Y+": 1.0 },
    var_99: 312443,
    cvar_99: 401221,
    var_95: 218341,
    pnl: -985752,
    pnl_pct: -0.0989,
  },
];

export const treasury = {
  as_of: "2025-04-17",
  regime: {
    regime: "inverted",
    slope_2s10s: -0.00486,
    butterfly: 0.00124,
    confidence: 0.87,
  },
  ns_params: {
    beta0: 0.0508,
    beta1: -0.0065,
    beta2: 0.0082,
    lambda1: 1.842,
    r2: 0.9987,
    rmse: 0.00014,
  },
  points: [
    { t: 0.083, y: 0.0531 },
    { t: 0.25, y: 0.0528 },
    { t: 0.5, y: 0.0521 },
    { t: 1, y: 0.0498 },
    { t: 2, y: 0.04798 },
    { t: 3, y: 0.04621 },
    { t: 5, y: 0.04512 },
    { t: 7, y: 0.04434 },
    { t: 10, y: 0.04312 },
    { t: 20, y: 0.04612 },
    { t: 30, y: 0.04534 },
  ],
  rates: {
    "0.25Y": 0.0528,
    "0.5Y": 0.0521,
    "1Y": 0.0498,
    "2Y": 0.04798,
    "3Y": 0.04621,
    "5Y": 0.04512,
    "7Y": 0.04434,
    "10Y": 0.04312,
    "20Y": 0.04612,
    "30Y": 0.04534,
  },
  spots: {
    "1Y": 0.04982,
    "2Y": 0.04812,
    "3Y": 0.04672,
    "5Y": 0.04554,
    "7Y": 0.04491,
    "10Y": 0.04381,
    "20Y": 0.04672,
    "30Y": 0.04601,
  },
  fwds: { "1x2": 0.04642, "2x5": 0.04389, "5x10": 0.04241, "10x30": 0.04812 },
};

export const benchmarkSpreads = [
  { rating: "AAA", oas: 12, ytm: 0.04432, n: 24 },
  { rating: "AA+", oas: 18, ytm: 0.04512, n: 41 },
  { rating: "AA", oas: 28, ytm: 0.04612, n: 63 },
  { rating: "AA-", oas: 38, ytm: 0.04712, n: 52 },
  { rating: "A+", oas: 52, ytm: 0.04862, n: 89 },
  { rating: "A", oas: 68, ytm: 0.05012, n: 124 },
  { rating: "A-", oas: 82, ytm: 0.05162, n: 97 },
  { rating: "BBB+", oas: 104, ytm: 0.05362, n: 145 },
  { rating: "BBB", oas: 128, ytm: 0.05612, n: 198 },
  { rating: "BBB-", oas: 162, ytm: 0.05962, n: 134 },
  { rating: "BB+", oas: 224, ytm: 0.06562, n: 112 },
  { rating: "BB", oas: 298, ytm: 0.07312, n: 86 },
  { rating: "B+", oas: 412, ytm: 0.08462, n: 67 },
  { rating: "B", oas: 554, ytm: 0.09862, n: 43 },
];

export const scenarios = [
  { name: "+100bps Parallel", p001: -688214, p002: -472834, p003: -852441 },
  { name: "-100bps Parallel", p001: 712481, p002: 491234, p003: 928812 },
  { name: "+200bps Parallel", p001: -1341284, p002: -928441, p003: -1641221 },
  { name: "-200bps Parallel", p001: 1498234, p002: 1012441, p003: 1982341 },
  { name: "Bear Flattener", p001: -142231, p002: -98412, p003: -921234 },
  { name: "Bull Steepener", p001: 156234, p002: 104812, p003: 984212 },
  { name: "Bear Twist +50", p001: -398412, p002: -264812, p003: -481234 },
  { name: "Bull Twist -50", p001: 412234, p002: 278812, p003: 501234 },
  { name: "+300bps Shock", p001: -1941284, p002: -1328441, p003: -2381221 },
  { name: "Credit +100bp", p001: -128441, p002: -341234, p003: -28412 },
];

// Generate rate history
function genHistory(base, seed, n = 180) {
  const labels = [],
    rates = [];
  const now = new Date("2025-04-17");
  let v = base;
  let count = 0;
  for (let i = n; i >= 0 && count < n; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    if (d.getDay() === 0 || d.getDay() === 6) continue;
    labels.push(d.toISOString().slice(0, 10));
    v += (Math.random() - 0.5 + seed) * 0.0006;
    v = Math.max(0.02, Math.min(0.08, v));
    rates.push(+v.toFixed(4));
    count++;
  }
  return { labels, rates };
}

export const history10y = genHistory(0.0431, -0.001);
export const history2y = genHistory(0.048, 0.001);
export const history5y = genHistory(0.0451, -0.0005);

// ML data
export const mlForecast = (() => {
  const labels = [],
    point = [],
    lower = [],
    upper = [];
  const now = new Date("2025-04-17");
  let v = 0.04312;
  for (let i = 0; i <= 60; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() + i);
    labels.push(d.toISOString().slice(0, 10));
    const t = i / 60;
    v =
      0.04312 +
      0.004 * (1 - Math.exp(-t)) * (Math.sin(t * Math.PI) * 0.6 - 0.3);
    const band = (0.003 * Math.sqrt(i + 1)) / Math.sqrt(61);
    point.push(+v.toFixed(4));
    lower.push(+(v - band * 1.645).toFixed(4));
    upper.push(+(v + band * 1.645).toFixed(4));
  }
  return { labels, point, lower, upper, backend: "transformer" };
})();

export const regimeData = {
  regime: "inverted",
  confidence: 0.87,
  probs: {
    inverted: 0.72,
    flat: 0.18,
    normal: 0.07,
    steep: 0.02,
    humped: 0.01,
  },
  features: {
    "Slope (2s10s)": 0.284,
    "Level (5Y)": 0.212,
    Volatility: 0.178,
    Momentum: 0.142,
    Butterfly: 0.108,
    "Level Δ (1M)": 0.076,
  },
};

export const garchData = (() => {
  const labels = [],
    vol = [];
  const now = new Date("2025-04-17");
  let v = 0.488;
  for (let i = 0; i <= 30; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() + i);
    labels.push(d.toISOString().slice(0, 10));
    v = v * 0.95 + 0.42 * 0.05 + (Math.random() - 0.5) * 0.02;
    vol.push(+Math.max(0.2, v).toFixed(3));
  }
  return { labels, vol, alpha: 0.0821, beta: 0.8934, omega: 0.000024 };
})();

export const pcaData = {
  variance: [0.821, 0.142, 0.028, 0.009],
  factors: ["Level", "Slope", "Curvature", "Residual"],
  loadings: {
    Level: {
      "1Y": 0.291,
      "2Y": 0.289,
      "3Y": 0.287,
      "5Y": 0.283,
      "7Y": 0.279,
      "10Y": 0.271,
      "20Y": 0.259,
      "30Y": 0.252,
    },
    Slope: {
      "1Y": -0.512,
      "2Y": -0.398,
      "3Y": -0.291,
      "5Y": -0.092,
      "7Y": 0.084,
      "10Y": 0.241,
      "20Y": 0.392,
      "30Y": 0.441,
    },
    Curvature: {
      "1Y": 0.401,
      "2Y": 0.212,
      "3Y": 0.042,
      "5Y": -0.234,
      "7Y": -0.298,
      "10Y": -0.184,
      "20Y": 0.121,
      "30Y": 0.312,
    },
  },
};

// Formatting helpers
export const fmt = {
  pct: (v, dp = 2) => (v == null ? "—" : (v * 100).toFixed(dp) + "%"),
  bps: (v) => (v == null ? "—" : (v * 10000).toFixed(1) + "bp"),
  money: (v) =>
    v == null
      ? "—"
      : "$" + Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 0 }),
  moneyM: (v) => (v == null ? "—" : "$" + (Math.abs(v) / 1e6).toFixed(2) + "M"),
  px: (v) => (v == null ? "—" : v.toFixed(3)),
  num: (v, dp = 2) => (v == null ? "—" : Number(v).toFixed(dp)),
  signM: (v) => {
    if (v == null) return "—";
    return (
      (v >= 0 ? "+$" : "-$") +
      Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 0 })
    );
  },
  signPct: (v) =>
    v == null ? "—" : (v >= 0 ? "+" : "") + (v * 100).toFixed(2) + "%",
};

export const ratingBadge = (r) => {
  if (!r) return "badge-gray";
  if (["AAA", "AA+", "AA", "AA-"].includes(r)) return "badge-green";
  if (["A+", "A", "A-"].includes(r)) return "badge-teal";
  if (["BBB+", "BBB", "BBB-"].includes(r)) return "badge-amber";
  return "badge-red";
};

export const bondTypeBadge = (t) =>
  ({
    fixed: "badge-indigo",
    callable: "badge-amber",
    floating: "badge-teal",
    zero_coupon: "badge-gray",
    inflation_linked: "badge-violet",
  })[t] || "badge-gray";

// Recharts theme
export const chartColors = {
  indigo: "#6366f1",
  teal: "#14b8a6",
  amber: "#f59e0b",
  green: "#10b981",
  red: "#ef4444",
  violet: "#a78bfa",
  sky: "#38bdf8",
};
export const chartTheme = {
  background: "transparent",
  grid: "rgba(99,120,180,0.12)",
  text: "#4e6080",
  tooltip: { bg: "#111927", border: "rgba(99,120,180,0.28)", text: "#f0f4ff" },
};
