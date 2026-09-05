import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import ErrorMessage from "../components/ErrorMessage";
import { IconSparkle, IconArrowRight, IconCheck } from "../components/Icons";

function Signup() {
  const navigate = useNavigate();
  const { signup } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!fullName || !email || !password) {
      setError("Please fill in all required fields.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setLoading(true);
    const res = await signup({
      full_name: fullName,
      email,
      password,
      role,
    });
    setLoading(false);

    if (!res.success) {
      setError(res.message || "Failed to create account.");
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
            Start your human-centered talent journey today.
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "1.05rem", marginTop: "14px", maxWidth: "460px" }}>
            Whether you are hiring top technical talent or mapping your engineering competencies, SkillBridge provides exact clarity.
          </p>
        </div>

        <div>
          <img
            src="/assets/hero_brand.jpg"
            alt="Collaborative engineering ecosystem"
            className="auth-hero-illustration"
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#e2e8f0", fontSize: "0.9rem" }}>
            <span style={{ color: "#10b981" }}><IconCheck size={16} /></span>
            <span>Deterministic skill gap analysis against live employer requirements</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#e2e8f0", fontSize: "0.9rem" }}>
            <span style={{ color: "#10b981" }}><IconCheck size={16} /></span>
            <span>Gated recruiter candidate inspection and instant pipeline shortlisting</span>
          </div>
        </div>
      </div>

      {/* Human Form Side */}
      <div className="auth-form-side">
        <div className="auth-form-card">
          <div style={{ marginBottom: "24px" }}>
            <div className="studio-badge" style={{ marginBottom: "8px" }}>
              <IconSparkle size={14} />
              <span>Get Started</span>
            </div>
            <h2 style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--ink-title)" }}>
              Create an account
            </h2>
            <p style={{ color: "var(--ink-muted)", fontSize: "0.925rem", marginTop: "4px" }}>
              Choose your profile track to configure your customized workspace.
            </p>
          </div>

          {error && <ErrorMessage message={error} />}

          <form onSubmit={handleSubmit}>
            {/* Human Role Selector Cards */}
            <div className="form-group">
              <label className="form-label">I am joining as a:</label>
              <div className="role-selector-human">
                <div
                  className={`role-card-btn ${role === "student" ? "active" : ""}`}
                  onClick={() => setRole("student")}
                >
                  <div className="role-card-title">Student / Candidate</div>
                  <div className="role-card-desc">Benchmark skills & unlock tailored upskilling paths</div>
                </div>

                <div
                  className={`role-card-btn ${role === "employer" ? "active" : ""}`}
                  onClick={() => setRole("employer")}
                >
                  <div className="role-card-title">Employer / Recruiter</div>
                  <div className="role-card-desc">Discover & shortlist candidates with verified skills</div>
                </div>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Full Legal Name</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. Maya Lin"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Work or Academic Email</label>
              <input
                type="email"
                className="form-control"
                placeholder="maya@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-control"
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>

            <div style={{ marginTop: "24px" }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
                style={{ width: "100%", padding: "12px 18px" }}
              >
                {loading ? "Creating your account..." : (
                  <>
                    <span>Complete Registration</span>
                    <IconArrowRight size={16} />
                  </>
                )}
              </button>
            </div>
          </form>

          <div style={{ marginTop: "24px", paddingTop: "20px", borderTop: "var(--border-hairline)", textAlign: "center", fontSize: "0.9rem", color: "var(--ink-muted)" }}>
            Already registered?{" "}
            <Link to="/login" style={{ fontWeight: 600 }}>
              Sign in to your account →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Signup;
