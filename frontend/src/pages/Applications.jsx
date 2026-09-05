import { useState, useEffect } from "react";
import { applicationApi } from "../services/api";
import { useAuth } from "../context/AuthContext";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";
import EmptyState from "../components/EmptyState";

function Applications() {
  const { user } = useAuth();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [actionLoading, setActionLoading] = useState({});

  const isRecruiter = user?.role === "employer" || user?.role === "admin";

  const fetchApplications = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await applicationApi.getApplications();
      setApplications(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load applications:", err);
      setError(err.message || "Failed to load applications.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleStatusChange = async (appId, newStatus) => {
    try {
      setActionLoading((prev) => ({ ...prev, [appId]: true }));
      await applicationApi.updateStatus(appId, newStatus);
      await fetchApplications();
    } catch (err) {
      alert(`Status transition failed: ${err.message || "Invalid transition"}`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [appId]: false }));
    }
  };

  const handleWithdraw = async (appId) => {
    if (!window.confirm("Are you sure you want to withdraw this application?")) return;
    try {
      setActionLoading((prev) => ({ ...prev, [appId]: true }));
      await applicationApi.withdrawApplication(appId);
      await fetchApplications();
    } catch (err) {
      alert(`Withdrawal failed: ${err.message}`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [appId]: false }));
    }
  };

  const filteredApps = applications.filter((app) => {
    if (statusFilter === "all") return true;
    return app.status?.toLowerCase() === statusFilter.toLowerCase();
  });

  const getStatusBadge = (status) => {
    const s = (status || "").toLowerCase();
    let badgeClass = "badge-neutral";
    if (s === "shortlisted") badgeClass = "badge-success";
    else if (s === "reviewed") badgeClass = "badge-info";
    else if (s === "rejected") badgeClass = "badge-danger";
    else if (s === "withdrawn") badgeClass = "badge-warning";
    else if (s === "submitted") badgeClass = "badge-primary";

    return <span className={`status-pill ${badgeClass}`}>{status}</span>;
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Job Applications</h1>
          <p className="page-subtitle">
            {isRecruiter
              ? "Review incoming candidates, evaluate snapshot match scores, and progress candidate pipelines."
              : "Track your active job submissions, employer review progress, and match evaluations."}
          </p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={fetchApplications} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {/* Filter Tabs */}
      <div className="filter-bar">
        {["all", "submitted", "reviewed", "shortlisted", "rejected", "withdrawn"].map((filter) => (
          <button
            key={filter}
            className={`filter-chip ${statusFilter === filter ? "active" : ""}`}
            onClick={() => setStatusFilter(filter)}
          >
            {filter.charAt(0).toUpperCase() + filter.slice(1)}
            <span className="chip-count">
              {filter === "all"
                ? applications.length
                : applications.filter((a) => a.status?.toLowerCase() === filter).length}
            </span>
          </button>
        ))}
      </div>

      {loading ? (
        <Loading />
      ) : filteredApps.length === 0 ? (
        <EmptyState
          title="No Applications Found"
          message={
            statusFilter === "all"
              ? "No job applications have been submitted yet."
              : `No applications with status "${statusFilter}".`
          }
        />
      ) : (
        <div className="card shadow-sm table-card">
          <div className="table-responsive">
            <table className="modern-table">
              <thead>
                <tr>
                  <th>Application ID</th>
                  <th>Job Title / ID</th>
                  <th>Candidate</th>
                  <th>Snapshot Match</th>
                  <th>Submitted On</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredApps.map((app) => (
                  <tr key={app.id}>
                    <td>
                      <span className="font-mono text-muted">#{app.id}</span>
                    </td>
                    <td>
                      <div className="font-semibold text-primary">
                        {app.job_title || `Job #${app.job_id}`}
                      </div>
                      <small className="text-muted">Job ID: {app.job_id}</small>
                    </td>
                    <td>
                      <div className="font-medium">{app.student_name || `Candidate #${app.student_id}`}</div>
                      <small className="text-muted">Student ID: {app.student_id}</small>
                    </td>
                    <td>
                      <div className="match-pill-container">
                        <span
                          className={`match-badge ${
                            (app.match_percentage_snapshot || 0) >= 70
                              ? "match-high"
                              : (app.match_percentage_snapshot || 0) >= 45
                              ? "match-mid"
                              : "match-low"
                          }`}
                        >
                          {Number(app.match_percentage_snapshot || 0).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td>
                      <small className="text-muted">
                        {app.created_at ? new Date(app.created_at).toLocaleDateString() : "Recent"}
                      </small>
                    </td>
                    <td>{getStatusBadge(app.status)}</td>
                    <td>
                      <div className="action-buttons-group">
                        {isRecruiter ? (
                          <>
                            {app.status === "submitted" && (
                              <button
                                className="btn btn-sm btn-outline-primary"
                                disabled={actionLoading[app.id]}
                                onClick={() => handleStatusChange(app.id, "reviewed")}
                              >
                                Mark Reviewed
                              </button>
                            )}
                            {(app.status === "submitted" || app.status === "reviewed") && (
                              <>
                                <button
                                  className="btn btn-sm btn-success"
                                  disabled={actionLoading[app.id]}
                                  onClick={() => handleStatusChange(app.id, "shortlisted")}
                                >
                                  Shortlist
                                </button>
                                <button
                                  className="btn btn-sm btn-outline-danger"
                                  disabled={actionLoading[app.id]}
                                  onClick={() => handleStatusChange(app.id, "rejected")}
                                >
                                  Reject
                                </button>
                              </>
                            )}
                            {(app.status === "shortlisted" || app.status === "rejected") && (
                              <button
                                className="btn btn-sm btn-ghost"
                                disabled={actionLoading[app.id]}
                                onClick={() => handleStatusChange(app.id, "closed")}
                              >
                                Close
                              </button>
                            )}
                          </>
                        ) : (
                          <>
                            {app.status === "submitted" && (
                              <button
                                className="btn btn-sm btn-outline-danger"
                                disabled={actionLoading[app.id]}
                                onClick={() => handleWithdraw(app.id)}
                              >
                                Withdraw
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Applications;
