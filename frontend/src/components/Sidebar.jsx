import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  IconDashboard,
  IconCandidates,
  IconBriefcase,
  IconTarget,
  IconRoadmap,
  IconApplications,
  IconLogout,
} from "./Icons";

function Sidebar() {
  const { user, logout } = useAuth();

  const userInitial = (user?.name || user?.email || "U")[0].toUpperCase();
  const userRole = user?.role || "user";

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-symbol">SB</div>
        <div className="brand-text">
          <span className="brand-title">SkillBridge</span>
          <span className="brand-subtitle">Talent Intelligence</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/dashboard" className={({ isActive }) => (isActive ? "active" : "")}>
          <IconDashboard size={19} />
          <span>Dashboard</span>
        </NavLink>

        <NavLink to="/students" className={({ isActive }) => (isActive ? "active" : "")}>
          <IconCandidates size={19} />
          <span>Candidates</span>
        </NavLink>

        <NavLink to="/jobs" className={({ isActive }) => (isActive ? "active" : "")}>
          <IconBriefcase size={19} />
          <span>Job Openings</span>
        </NavLink>

        <NavLink to="/analysis" className={({ isActive }) => (isActive ? "active" : "")}>
          <IconTarget size={19} />
          <span>Skill Analysis</span>
        </NavLink>

        <NavLink to="/recommendations" className={({ isActive }) => (isActive ? "active" : "")}>
          <IconRoadmap size={19} />
          <span>Recommendations</span>
        </NavLink>

        <NavLink to="/applications" className={({ isActive }) => (isActive ? "active" : "")}>
          <IconApplications size={19} />
          <span>Applications</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile-strip">
          <div className="user-avatar-initial">{userInitial}</div>
          <div className="user-info-meta">
            <div className="user-name-label">{user?.name || user?.email}</div>
            <div className="user-role-tag">{userRole}</div>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={logout}
            title="Sign out of account"
            style={{ color: "#94a3b8", padding: "6px" }}
          >
            <IconLogout size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
