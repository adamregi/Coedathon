import { useAuth } from "../context/AuthContext";
import { IconLogout } from "./Icons";

function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="header">
      <div className="header-left">
        <div className="system-status-indicator">
          <span className="status-pulse-dot" />
          <span>Live Talent Engine</span>
        </div>
      </div>

      <div className="header-right">
        {user && (
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--ink-muted)" }}>
              {user.name || user.email}
            </span>
            <span
              style={{
                fontSize: "0.725rem",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                backgroundColor: "var(--brand-primary-soft)",
                color: "var(--brand-primary)",
                padding: "3px 8px",
                borderRadius: "var(--radius-full)",
              }}
            >
              {user.role || "User"}
            </span>
          </div>
        )}

        <button
          className="btn btn-secondary btn-sm"
          onClick={logout}
          title="Sign out of account"
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <IconLogout size={15} />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
}

export default Header;
