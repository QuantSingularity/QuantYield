import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, AlertCircle, CheckCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import "./auth.css";

const PLANS = [
  {
    id: "starter",
    name: "Starter",
    price: "$299/mo",
    desc: "500 bonds · 3 portfolios",
  },
  {
    id: "pro",
    name: "Pro",
    price: "$799/mo",
    desc: "Unlimited · Full AI suite",
    highlight: true,
  },
  {
    id: "trial",
    name: "Free Trial",
    price: "$0 / 14 days",
    desc: "No credit card required",
  },
];

export default function Register() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    firm: "",
    role: "",
    password: "",
    confirmPw: "",
    plan: "trial",
  });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { register } = useAuth();
  const navigate = useNavigate();

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const pwStrength = () => {
    const p = form.password;
    if (!p) return 0;
    let s = 0;
    if (p.length >= 8) s++;
    if (/[A-Z]/.test(p)) s++;
    if (/[0-9]/.test(p)) s++;
    if (/[^A-Za-z0-9]/.test(p)) s++;
    return s;
  };

  const strength = pwStrength();
  const strengthLabel = ["", "Weak", "Fair", "Good", "Strong"][strength];
  const strengthColor = ["", "#ef4444", "#f59e0b", "#10b981", "#14b8a6"][
    strength
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirmPw)
      return setError("Passwords do not match");
    if (strength < 2) return setError("Please use a stronger password");
    setLoading(true);
    await new Promise((r) => setTimeout(r, 700));
    const result = register(form);
    setLoading(false);
    if (result.ok) navigate("/app/dashboard");
    else setError(result.error);
  };

  return (
    <div className="auth-shell">
      <div className="auth-glow auth-glow-1" />
      <div className="auth-glow auth-glow-2" />

      {/* Left panel */}
      <div className="auth-panel auth-left">
        <Link to="/" className="auth-logo">
          <div className="auth-logo-mark">
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
          <span>QuantYield</span>
        </Link>

        <div className="auth-tagline">
          <h2 className="auth-tagline-title">Start your free trial</h2>
          <p className="auth-tagline-sub">
            Get full access to all platform features for 14 days, no credit card
            required.
          </p>
        </div>

        {/* Plan selector */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
            marginTop: 4,
          }}
        >
          {PLANS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setForm((f) => ({ ...f, plan: p.id }))}
              className={`auth-plan-btn ${form.plan === p.id ? "selected" : ""}`}
            >
              <div style={{ flex: 1 }}>
                <div className="auth-plan-name">
                  {p.name}{" "}
                  {p.highlight && (
                    <span className="auth-plan-badge">Popular</span>
                  )}
                </div>
                <div className="auth-plan-desc">{p.desc}</div>
              </div>
              <div className="auth-plan-price">{p.price}</div>
              {form.plan === p.id && (
                <CheckCircle
                  size={15}
                  color="var(--indigo-400)"
                  style={{ flexShrink: 0 }}
                />
              )}
            </button>
          ))}
        </div>

        <div className="auth-left-footer">
          <span>
            Already have an account?{" "}
            <Link to="/login" className="auth-link">
              Sign in
            </Link>
          </span>
        </div>
      </div>

      {/* Right panel */}
      <div className="auth-panel auth-right">
        <div className="auth-form-wrap">
          <div className="auth-form-header">
            <h1 className="auth-form-title">Create your account</h1>
            <p className="auth-form-sub">
              Get started with QuantYield in seconds.
            </p>
          </div>

          {error && (
            <div className="auth-error">
              <AlertCircle size={14} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 12,
              }}
            >
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Jane Smith"
                  value={form.name}
                  onChange={set("name")}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Firm / Organisation</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Blackrock Capital"
                  value={form.firm}
                  onChange={set("firm")}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Work Email</label>
              <input
                type="email"
                className="form-control"
                placeholder="jane@firm.com"
                value={form.email}
                onChange={set("email")}
                autoComplete="email"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Role</label>
              <select
                className="form-control"
                value={form.role}
                onChange={set("role")}
              >
                <option value="">Select your role…</option>
                <option>Portfolio Manager</option>
                <option>Quant Analyst</option>
                <option>Risk Manager</option>
                <option>Fixed Income Trader</option>
                <option>Research Analyst</option>
                <option>Developer</option>
                <option>Other</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <div className="auth-pw-field">
                <input
                  type={showPw ? "text" : "password"}
                  className="form-control"
                  placeholder="Min. 8 characters"
                  value={form.password}
                  onChange={set("password")}
                  autoComplete="new-password"
                  required
                  style={{ paddingRight: 40 }}
                />
                <button
                  type="button"
                  className="auth-pw-toggle"
                  onClick={() => setShowPw((p) => !p)}
                >
                  {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {form.password && (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    marginTop: 6,
                  }}
                >
                  <div
                    style={{
                      flex: 1,
                      height: 3,
                      background: "var(--border)",
                      borderRadius: 2,
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        width: `${strength * 25}%`,
                        height: "100%",
                        background: strengthColor,
                        borderRadius: 2,
                        transition: "all 0.3s ease",
                      }}
                    />
                  </div>
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 600,
                      color: strengthColor,
                      minWidth: 36,
                    }}
                  >
                    {strengthLabel}
                  </span>
                </div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <input
                type="password"
                className="form-control"
                placeholder="Re-enter password"
                value={form.confirmPw}
                onChange={set("confirmPw")}
                autoComplete="new-password"
                required
                style={{
                  borderColor:
                    form.confirmPw && form.confirmPw !== form.password
                      ? "var(--red)"
                      : undefined,
                }}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg auth-submit"
              disabled={loading}
            >
              {loading ? (
                <span
                  className="animate-spin"
                  style={{
                    display: "inline-block",
                    width: 16,
                    height: 16,
                    border: "2px solid rgba(255,255,255,0.3)",
                    borderTopColor: "white",
                    borderRadius: "50%",
                  }}
                />
              ) : (
                `Create Account · ${PLANS.find((p) => p.id === form.plan)?.name || "Free Trial"}`
              )}
            </button>
          </form>

          <p className="auth-consent">
            By creating an account you agree to our{" "}
            <a href="#" className="auth-link">
              Terms
            </a>{" "}
            and{" "}
            <a href="#" className="auth-link">
              Privacy Policy
            </a>
            . SOC 2 Type II certified.
          </p>
        </div>
      </div>
    </div>
  );
}
