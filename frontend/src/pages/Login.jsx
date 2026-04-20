import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, TrendingUp, AlertCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import "./auth.css";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    await new Promise((r) => setTimeout(r, 600));
    const result = login(email, password);
    setLoading(false);
    if (result.ok) navigate("/app/dashboard");
    else setError(result.error);
  };

  return (
    <div className="auth-shell">
      {/* Background glows */}
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
          <h2 className="auth-tagline-title">Welcome back</h2>
          <p className="auth-tagline-sub">
            Sign in to access your fixed income analytics platform.
          </p>
        </div>

        <div className="auth-features">
          {[
            { icon: "📊", text: "Real-time yield curve analytics" },
            { icon: "🤖", text: "AI-powered rate forecasting" },
            { icon: "🛡️", text: "Portfolio VaR & scenario analysis" },
          ].map((f) => (
            <div key={f.text} className="auth-feature-item">
              <span className="auth-feature-icon">{f.icon}</span>
              <span className="auth-feature-text">{f.text}</span>
            </div>
          ))}
        </div>

        <div className="auth-left-footer">
          <span>© 2025 QuantYield Inc.</span>
          <div className="auth-left-links">
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
          </div>
        </div>
      </div>

      {/* Right panel */}
      <div className="auth-panel auth-right">
        <div className="auth-form-wrap">
          <div className="auth-form-header">
            <h1 className="auth-form-title">Sign in to your account</h1>
            <p className="auth-form-sub">
              Don't have an account?{" "}
              <Link to="/register" className="auth-link">
                Create one free
              </Link>
            </p>
          </div>

          {error && (
            <div className="auth-error">
              <AlertCircle size={14} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label className="form-label">Email address</label>
              <input
                type="email"
                className="form-control"
                placeholder="you@firm.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>

            <div className="form-group">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 6,
                }}
              >
                <label className="form-label">Password</label>
                <a href="#" className="auth-link" style={{ fontSize: 11 }}>
                  Forgot password?
                </a>
              </div>
              <div className="auth-pw-field">
                <input
                  type={showPw ? "text" : "password"}
                  className="form-control"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
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
                "Sign in"
              )}
            </button>
          </form>

          <div className="auth-divider">
            <span>or continue with</span>
          </div>

          <div className="auth-socials">
            <button
              className="auth-social-btn"
              onClick={() => {
                setEmail("demo@quantyield.io");
                setPassword("demo1234");
              }}
            >
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>
                📧
              </span>
              Use demo credentials
            </button>
          </div>

          <p className="auth-consent">
            By signing in, you agree to our{" "}
            <a href="#" className="auth-link">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="#" className="auth-link">
              Privacy Policy
            </a>
            .
          </p>
        </div>
      </div>
    </div>
  );
}
