import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import ErrorMessage from "../components/ErrorMessage";
import { IconSparkle, IconArrowRight } from "../components/Icons";

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Please provide both your registered email address and password.");
      return;
    }

    setLoading(true);
    const result = await login(email, password);
    setLoading(false);

    if (!result.success) {
      setError(result.message || "Invalid email or password.");
      return;
    }

    navigate("/dashboard");
  };

  return (
    <div className="auth-split-layout">
      {/* Editorial Brand Side */}
      <div className="auth-brand-side">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "32px" }}>
            <div className="brand-symbol">SB</div>
            <span style={{ fontSize: "1.3rem", fontWeight: 800, color: "#ffffff", letterSpacing: "-0.03em" }}>
              SkillBridge
            </span>
          </div>

          <h1 style={{ fontSize: "2.4rem", fontWeight: 800, color: "#ffffff", lineHeight: 1.15, maxWidth: "480px" }}>
            Bridging talent potential with verified engineering reality.
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "1.05rem", marginTop: "14px", maxWidth: "460px" }}>
            Evaluate authentic candidate competencies, run deterministic skill gap benchmarks, and discover the exact right fit.
          </p>
        </div>

        <div>
          <img
            src="/assets/hero_brand.jpg"
            alt="Collaborative engineering and talent discovery"
            className="auth-hero-illustration"
          />
        </div>

        <div>
          <div className="auth-quote-box">
            "We replaced resume buzzword guesswork with deterministic proficiency math. Hiring speed increased tenfold."
          </div>
          <div style={{ fontSize: "0.85rem", color: "#94a3b8" }}>
            Engineering Talent Benchmark — Verified against production datasets
          </div>
        </div>
      </div>

      {/* Human Form Side */}
      <div className="auth-form-side">
        <div className="auth-form-card">
          <div style={{ marginBottom: "26px" }}>
            <div className="studio-badge" style={{ marginBottom: "8px" }}>
              <IconSparkle size={14} />
              <span>Authentication</span>
            </div>
            <h2 style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--ink-title)" }}>
              Welcome back
            </h2>
            <p style={{ color: "var(--ink-muted)", fontSize: "0.925rem", marginTop: "4px" }}>
              Sign in to access candidate discovery, gap analyses, and live talent pipelines.
            </p>
          </div>

          {error && <ErrorMessage message={error} />}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-control"
                placeholder="e.g. recruiter@company.com or student@univ.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label className="form-label">Password</label>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{ fontSize: "0.75rem", color: "var(--brand-primary)", fontWeight: 600 }}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
              <input
                type={showPassword ? "text" : "password"}
                className="form-control"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            <div style={{ marginTop: "24px" }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
                style={{ width: "100%", padding: "12px 18px" }}
              >
                {loading ? "Signing in..." : (
                  <>
                    <span>Sign In to SkillBridge</span>
                    <IconArrowRight size={16} />
                  </>
                )}
              </button>
            </div>
          </form>

          <div style={{ marginTop: "24px", paddingTop: "20px", borderTop: "var(--border-hairline)", textAlign: "center", fontSize: "0.9rem", color: "var(--ink-muted)" }}>
            New to SkillBridge?{" "}
            <Link to="/signup" style={{ fontWeight: 600 }}>
              Create an account →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
