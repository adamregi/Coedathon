import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { jobApi, applicationApi } from "../services/api";

function Jobs() {
  const { isEmployer } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [applyMessage, setApplyMessage] = useState("");

  async function loadJobs() {
    try {
      const res = await jobApi.getJobs();
      const list = Array.isArray(res) ? res : res.data || [];
      setJobs(list);
    } catch (err) {
      setError(err.message || "Failed to load jobs.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadJobs();
  }, []);

  const handleApply = async (jobId, title) => {
    try {
      await applicationApi.submitApplication(jobId);
      setApplyMessage(`Successfully applied to ${title}! Match snapshot preserved.`);
    } catch (err) {
      setApplyMessage(`Application note: ${err.message}`);
    }
    setTimeout(() => setApplyMessage(""), 5000);
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1>Active Job Openings</h1>
          <p>Explore opportunities and compare your skill compatibility</p>
        </div>

        {isEmployer && (
          <Link to="/jobs/add" className="btn-primary">
            + Post New Job
          </Link>
        )}
      </div>

      {error && <div className="alert-error-banner">{error}</div>}
      {applyMessage && <div className="alert-success-banner">{applyMessage}</div>}

      {loading ? (
        <div className="loading-state-card">
          <div className="spinner"></div>
          <p>Loading jobs from database...</p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="empty-talent-card">
          <div className="empty-icon">💼</div>
          <h3>No jobs posted yet</h3>
          <p>Employers can click "Post New Job" above to create open requisitions.</p>
        </div>
      ) : (
        <div className="table-responsive">
          <table className="custom-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Job Title</th>
                <th>Company</th>
                <th>Location / Dept</th>
                <th>Required Skills</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>#{job.id}</td>
                  <td>
                    <strong>{job.title}</strong>
                  </td>
                  <td>{job.company_name}</td>
                  <td>
                    {job.location || "Remote"} {job.department && `• ${job.department}`}
                  </td>
                  <td>
                    <span className="badge-skill-count">
                      {job.requirements?.length || job.skills?.length || 0} Skills
                    </span>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <Link to={`/jobs/${job.id}`} className="btn-outline-sm">
                        Details & Skills
                      </Link>
                      {isEmployer ? (
                        <Link
                          to={`/dashboard?jobId=${job.id}`}
                          className="btn-primary-sm"
                          title="Discover & search candidates matching this requisition"
                          style={{ textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px" }}
                        >
                          🔍 Match Candidates
                        </Link>
                      ) : (
                        <button
                          className="btn-primary-sm"
                          onClick={() => handleApply(job.id, job.title)}
                        >
                          Apply Now
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Jobs;
