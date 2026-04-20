import { Link } from "react-router-dom";
import {
  TrendingUp,
  Shield,
  Zap,
  BarChart3,
  Brain,
  ArrowRight,
  CheckCircle,
  ChevronRight,
} from "lucide-react";
import "./landing.css";

const FEATURES = [
  {
    icon: TrendingUp,
    color: "#6366f1",
    title: "Bond Analytics",
    desc: "Full dirty/clean pricing, YTM solving, Macaulay & modified duration, DV01, convexity and key rate durations across 10 tenors.",
  },
  {
    icon: BarChart3,
    color: "#14b8a6",
    title: "Yield Curve Modelling",
    desc: "Nelson-Siegel, Svensson, Bootstrap and Cubic Spline fitting against live FRED data with R² and RMSE diagnostics.",
  },
  {
    icon: Shield,
    color: "#10b981",
    title: "Portfolio Risk",
    desc: "Historical & parametric VaR/CVaR, scenario analysis (10 standard shocks), DV01-based P&L attribution and CS01 sensitivity.",
  },
  {
    icon: Brain,
    color: "#a78bfa",
    title: "AI Forecasting",
    desc: "Transformer/LSTM/AR(1) rate forecasting, GARCH volatility, XGBoost credit spread prediction and ML regime classification.",
  },
  {
    icon: Zap,
    color: "#f59e0b",
    title: "Spread Analytics",
    desc: "Z-spread, Monte Carlo OAS for callable bonds, benchmark spread matrices and IG/HY implied yield curves.",
  },
  {
    icon: BarChart3,
    color: "#38bdf8",
    title: "PCA Factor Models",
    desc: "Curve decomposition into Level, Slope and Curvature factors with loading matrices and time-series of factor scores.",
  },
];

const PRICING = [
  {
    name: "Starter",
    price: "$299",
    period: "/mo",
    desc: "For individual analysts and small teams.",
    features: [
      "Up to 500 bonds",
      "3 portfolios",
      "Yield curve analytics",
      "API access (10k req/mo)",
      "Email support",
    ],
    highlight: false,
  },
  {
    name: "Pro",
    price: "$799",
    period: "/mo",
    desc: "Full platform access for portfolio managers.",
    features: [
      "Unlimited bonds",
      "25 portfolios",
      "Full AI/ML suite",
      "VaR & scenario engine",
      "API access (unlimited)",
      "Priority support",
      "SSO",
    ],
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    desc: "Dedicated deployment and white-glove onboarding.",
    features: [
      "Everything in Pro",
      "On-premise deployment",
      "Custom ML models",
      "Bloomberg / Refinitiv feed",
      "SLA guarantee",
      "Dedicated CSM",
    ],
    highlight: false,
  },
];

const STATS = [
  { value: "$2.4T", label: "AUM Monitored" },
  { value: "380+", label: "Institutional Clients" },
  { value: "99.97%", label: "API Uptime" },
  { value: "<50ms", label: "Median Latency" },
];

export default function Landing() {
  return (
    <div className="landing">
      {/* Nav */}
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <div className="landing-logo">
            <div className="landing-logo-mark">
              <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
                <path
                  d="M6 24L12 10L18 17L23 7"
                  stroke="white"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <circle cx="23" cy="7" r="3" fill="#14b8a6" />
              </svg>
            </div>
            <span className="landing-logo-name">QuantYield</span>
          </div>
          <div className="landing-nav-links">
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <a href="#about">About</a>
          </div>
          <div className="landing-nav-actions">
            <Link to="/login" className="btn btn-ghost btn-sm">
              Sign in
            </Link>
            <Link to="/register" className="btn btn-primary btn-sm">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="landing-hero">
        <div className="hero-glow hero-glow-1" />
        <div className="hero-glow hero-glow-2" />
        <div className="hero-glow hero-glow-3" />
        <div className="landing-container">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            Now with Transformer-based rate forecasting
            <ChevronRight size={13} />
          </div>
          <h1 className="hero-headline">
            Institutional Fixed Income
            <br />
            <span className="hero-headline-accent">Analytics Platform</span>
          </h1>
          <p className="hero-sub">
            Bond pricing engines, yield curve modelling, portfolio risk
            analytics, and AI-powered forecasting — built for quants, portfolio
            managers, and risk teams.
          </p>
          <div className="hero-actions">
            <Link to="/register" className="btn btn-primary btn-lg hero-cta">
              Start Free Trial <ArrowRight size={16} />
            </Link>
            <Link to="/login" className="btn btn-secondary btn-lg">
              View Demo
            </Link>
          </div>
          <div className="hero-note">
            No credit card required · 14-day free trial · SOC 2 Type II
            certified
          </div>
        </div>

        {/* Mock dashboard preview */}
        <div className="hero-preview">
          <div className="landing-container">
            <div className="preview-window">
              <div className="preview-bar">
                <div
                  className="preview-dot"
                  style={{ background: "#ef4444" }}
                />
                <div
                  className="preview-dot"
                  style={{ background: "#f59e0b" }}
                />
                <div
                  className="preview-dot"
                  style={{ background: "#10b981" }}
                />
                <span
                  style={{
                    fontSize: 11,
                    color: "var(--text-muted)",
                    marginLeft: "auto",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  quantyield.io/app/dashboard
                </span>
              </div>
              <div className="preview-body">
                <div className="preview-kpis">
                  {[
                    ["AUM", "$32.8M", "↑ 2.1%", "var(--green)"],
                    ["YTM", "4.821%", "−12bp", "var(--red)"],
                    ["Duration", "5.84Y", "", ""],
                    ["VaR 99%", "$142K", "1-day", ""],
                  ].map(([l, v, d, c]) => (
                    <div key={l} className="preview-kpi">
                      <div className="preview-kpi-label">{l}</div>
                      <div className="preview-kpi-value">{v}</div>
                      {d && (
                        <div
                          style={{
                            fontSize: 10,
                            color: c || "var(--text-muted)",
                            fontFamily: "var(--font-mono)",
                          }}
                        >
                          {d}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                <div className="preview-chart">
                  <svg
                    viewBox="0 0 400 90"
                    preserveAspectRatio="none"
                    style={{ width: "100%", height: "100%" }}
                  >
                    <defs>
                      <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
                        <stop
                          offset="0%"
                          stopColor="#6366f1"
                          stopOpacity="0.3"
                        />
                        <stop
                          offset="100%"
                          stopColor="#6366f1"
                          stopOpacity="0"
                        />
                      </linearGradient>
                    </defs>
                    <path
                      d="M0,70 C30,65 60,55 90,58 C120,61 150,48 180,45 C210,42 240,50 270,44 C300,38 330,32 360,35 C380,37 400,30 400,30 L400,90 L0,90Z"
                      fill="url(#cg)"
                    />
                    <path
                      d="M0,70 C30,65 60,55 90,58 C120,61 150,48 180,45 C210,42 240,50 270,44 C300,38 330,32 360,35 C380,37 400,30 400,30"
                      fill="none"
                      stroke="#6366f1"
                      strokeWidth="2"
                    />
                    <path
                      d="M0,75 C40,70 80,75 120,68 C160,61 200,72 240,65 C280,58 320,62 360,55 C380,52 400,50 400,50"
                      fill="none"
                      stroke="#14b8a6"
                      strokeWidth="1.5"
                      strokeDasharray="4,3"
                      opacity="0.7"
                    />
                  </svg>
                </div>
                <div className="preview-table-rows">
                  {[
                    ["US Treasury 4.5% 2034", "AAA", "4.621%", "8.12Y"],
                    ["Apple Inc 3.85% 2043", "AA+", "5.012%", "14.21Y"],
                    ["JPMorgan 5.1% 2028", "A−", "5.145%", "4.23Y"],
                  ].map(([n, r, y, d]) => (
                    <div key={n} className="preview-row">
                      <span
                        style={{
                          flex: 1,
                          fontSize: 10.5,
                          color: "var(--text-primary)",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {n}
                      </span>
                      <span
                        style={{
                          padding: "1px 6px",
                          borderRadius: 20,
                          fontSize: 9,
                          background: "var(--green-glow)",
                          color: "var(--green)",
                          border: "1px solid rgba(16,185,129,0.2)",
                          fontWeight: 600,
                          flexShrink: 0,
                        }}
                      >
                        {r}
                      </span>
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: 10.5,
                          color: "var(--teal-400)",
                          minWidth: 48,
                          textAlign: "right",
                        }}
                      >
                        {y}
                      </span>
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: 10.5,
                          color: "var(--text-secondary)",
                          minWidth: 40,
                          textAlign: "right",
                        }}
                      >
                        {d}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="landing-stats">
        <div className="landing-container">
          <div className="stats-grid">
            {STATS.map((s) => (
              <div key={s.label} className="stat-block">
                <div className="stat-block-value">{s.value}</div>
                <div className="stat-block-label">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="landing-section">
        <div className="landing-container">
          <div className="section-header">
            <div className="section-tag">Platform Capabilities</div>
            <h2 className="section-title">Everything your desk needs</h2>
            <p className="section-desc">
              Institutional-grade quant models, clean REST API, and AI-powered
              analytics — all in one platform.
            </p>
          </div>
          <div className="features-grid">
            {FEATURES.map((f) => (
              <div key={f.title} className="feature-card">
                <div
                  className="feature-icon"
                  style={{
                    background: f.color + "18",
                    border: `1px solid ${f.color}28`,
                  }}
                >
                  <f.icon size={20} color={f.color} />
                </div>
                <h3 className="feature-title">{f.title}</h3>
                <p className="feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="landing-section landing-section-alt">
        <div className="landing-container">
          <div className="section-header">
            <div className="section-tag">Pricing</div>
            <h2 className="section-title">Simple, transparent pricing</h2>
          </div>
          <div className="pricing-grid">
            {PRICING.map((p) => (
              <div
                key={p.name}
                className={`pricing-card ${p.highlight ? "pricing-card-highlight" : ""}`}
              >
                {p.highlight && (
                  <div className="pricing-badge">Most Popular</div>
                )}
                <div className="pricing-name">{p.name}</div>
                <div className="pricing-price">
                  <span className="pricing-amount">{p.price}</span>
                  <span className="pricing-period">{p.period}</span>
                </div>
                <p className="pricing-desc">{p.desc}</p>
                <div className="pricing-divider" />
                <ul className="pricing-features">
                  {p.features.map((f) => (
                    <li key={f}>
                      <CheckCircle
                        size={13}
                        color="var(--green)"
                        style={{ flexShrink: 0 }}
                      />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to="/register"
                  className={`btn ${p.highlight ? "btn-primary" : "btn-secondary"} btn-lg`}
                  style={{ width: "100%", marginTop: "auto" }}
                >
                  {p.name === "Enterprise"
                    ? "Contact Sales"
                    : "Start Free Trial"}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="landing-cta">
        <div className="cta-glow" />
        <div className="landing-container">
          <h2 className="cta-title">Ready to get started?</h2>
          <p className="cta-desc">
            Join 380+ institutional teams using QuantYield to manage fixed
            income risk.
          </p>
          <div className="cta-actions">
            <Link to="/register" className="btn btn-primary btn-lg">
              Create Free Account <ArrowRight size={16} />
            </Link>
            <Link to="/login" className="btn btn-secondary btn-lg">
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-container">
          <div className="footer-top">
            <div className="landing-logo">
              <div className="landing-logo-mark">
                <svg width="18" height="18" viewBox="0 0 32 32" fill="none">
                  <path
                    d="M6 24L12 10L18 17L23 7"
                    stroke="white"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <circle cx="23" cy="7" r="3" fill="#14b8a6" />
                </svg>
              </div>
              <span className="landing-logo-name">QuantYield</span>
            </div>
            <div className="footer-links">
              {[
                "Features",
                "Pricing",
                "API Docs",
                "Security",
                "Blog",
                "Careers",
              ].map((l) => (
                <a key={l} href="#">
                  {l}
                </a>
              ))}
            </div>
          </div>
          <div className="footer-bottom">
            <span>© 2025 QuantYield Inc. All rights reserved.</span>
            <span style={{ color: "var(--text-muted)", fontSize: 11 }}>
              SOC 2 Type II · GDPR Compliant · ISO 27001
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
