import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { jobApi, skillApi, applicationApi } from "../services/api";

function JobDetails() {
  const { id } = useParams();
  const { isEmployer } = useAuth();

  const [job, setJob] = useState(null);
  const [requirements, setRequirements] = useState([]);
  const [catalogSkills, setCatalogSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  // Add requirement state
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [requiredLevel, setRequiredLevel] = useState(3);
  const [mandatory, setMandatory] = useState(true);
  const [submittingReq, setSubmittingReq] = useState(false);

  async function loadJobData() {
    try {
      const [jobData, reqsData, catalogData] = await Promise.allSettled([
        jobApi.getJob(id),
        jobApi.getRequirements(id),
        skillApi.getSkills(),
      ]);

      if (jobData.status === "fulfilled" && jobData.value) {
        setJob(jobData.value);
      }
      if (reqsData.status === "fulfilled" && reqsData.value) {
        const list = Array.isArray(reqsData.value) ? reqsData.value : reqsData.value.data || [];
        setRequirements(list);
      }
      if (catalogData.status === "fulfilled" && catalogData.value) {
        const cList = Array.isArray(catalogData.value) ? catalogData.value : catalogData.value.data || [];
        setCatalogSkills(cList);
        if (cList.length > 0) setSelectedSkillId(String(cList[0].id));
      }
    } catch (err) {
      setError("Failed to load job details.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadJobData();
  }, [id]);

  const handleAddRequirement = async (e) => {
    e.preventDefault();
    if (!selectedSkillId) return;

    setSubmittingReq(true);
    setError("");
    setMessage("");

    try {
      await jobApi.addRequirement(id, {
        skill_id: Number(selectedSkillId),
        required_level: Number(requiredLevel),
        mandatory,
      });
      setMessage("Skill requirement updated successfully!");
      await loadJobData();
    } catch (err) {
      setError(err.message || "Failed to add requirement");
    } finally {
      setSubmittingReq(false);
    }
  };

  const handleDeleteRequirement = async (skillId) => {
    try {
      await jobApi.deleteRequirement(id, skillId);
      setMessage("Requirement removed.");
      await loadJobData();
    } catch (err) {
      setError(err.message || "Failed to remove requirement");
    }
  };

  const handleApply = async () => {
    try {
      await applicationApi.submitApplication(id);
      setMessage("Application submitted successfully! Match snapshot saved.");
    } catch (err) {
      setError(err.message || "Application failed");
    }
  };

  if (loading) {
    return (
      <div className="loading-state-card">
        <div className="spinner"></div>
        <p>Loading job requirements...</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="empty-talent-card">
        <h3>Job not found</h3>
        <Link to="/jobs" className="btn-primary">
          ← Back to Jobs
        </Link>
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1>{job.title}</h1>
          <p>
            {job.company_name} • {job.location || "Remote"} • {job.department || "Engineering"}
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          {isEmployer ? (
            <Link
              to={`/dashboard?jobId=${id}`}
              className="btn-primary"
              style={{ textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "6px" }}
            >
              🔍 Discover & Filter Matching Candidates
            </Link>
          ) : (
            <button className="btn-primary" onClick={handleApply}>
              ⚡ Apply for Position
            </button>
          )}
          <Link to="/jobs" className="btn-secondary">
            ← Back to Jobs
          </Link>
        </div>
      </div>

      {error && <div className="alert-error-banner">{error}</div>}
      {message && <div className="alert-success-banner">{message}</div>}

      <div className="profile-hero-card">
        <div>
          <h3>Job Description</h3>
          <p style={{ marginTop: "0.5rem", color: "#475569", lineHeight: "1.6" }}>
            {job.description || "No description provided for this opening."}
          </p>
          {job.salary_range && (
            <p style={{ marginTop: "0.5rem", fontWeight: "bold" }}>
              💰 Target Compensation: {job.salary_range}
            </p>
          )}
        </div>
      </div>

      {/* Recruiter Requirement Editor */}
      {isEmployer && (
        <div className="dashboard-section" style={{ marginTop: "1.5rem" }}>
          <h3>Add / Update Skill Requirement</h3>
          <form className="inline-add-skill-form" onSubmit={handleAddRequirement}>
            <div className="form-group" style={{ flex: 2 }}>
              <label>Skill:</label>
              <select
                value={selectedSkillId}
                onChange={(e) => setSelectedSkillId(e.target.value)}
                className="custom-select"
              >
                {catalogSkills.map((sk) => (
                  <option key={sk.id} value={sk.id}>
                    {sk.name} ({sk.category || "General"})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ flex: 1 }}>
              <label>Required Level (1-5):</label>
              <select
                value={requiredLevel}
                onChange={(e) => setRequiredLevel(e.target.value)}
                className="custom-select"
              >
                <option value="1">Level 1 - Novice</option>
                <option value="2">Level 2 - Beginner</option>
                <option value="3">Level 3 - Intermediate</option>
                <option value="4">Level 4 - Advanced</option>
                <option value="5">Level 5 - Expert</option>
              </select>
            </div>

            <div className="form-group" style={{ flex: 1 }}>
              <label>Importance:</label>
              <select
                value={mandatory ? "true" : "false"}
                onChange={(e) => setMandatory(e.target.value === "true")}
                className="custom-select"
              >
                <option value="true">Mandatory (2x Weight)</option>
                <option value="false">Optional (1x Weight)</option>
              </select>
            </div>

            <button type="submit" className="btn-primary" disabled={submittingReq} style={{ alignSelf: "flex-end" }}>
              {submittingReq ? "Saving..." : "+ Save Requirement"}
            </button>
          </form>
        </div>
      )}

      {/* Required Skills Table */}
      <div className="dashboard-section" style={{ marginTop: "1.5rem" }}>
        <h3>Required Job Competencies ({requirements.length})</h3>

        {requirements.length === 0 ? (
          <div className="empty-talent-card">
            <p>No skill requirements specified for this position yet.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Skill Name</th>
                  <th>Category</th>
                  <th>Required Proficiency</th>
                  <th>Requirement Type</th>
                  {isEmployer && <th>Action</th>}
                </tr>
              </thead>
              <tbody>
                {requirements.map((req) => (
                  <tr key={req.id || req.skill_id}>
                    <td>
                      <strong>{req.skill_name || `Skill #${req.skill_id}`}</strong>
                    </td>
                    <td>
                      <span className="badge-category">{req.category || "General"}</span>
                    </td>
                    <td>
                      <span className="badge-proficiency">Level {req.required_level || req.required_proficiency} of 5</span>
                    </td>
                    <td>
                      <span
                        className={
                          req.mandatory
                            ? "badge-req-mandatory"
                            : "badge-req-optional"
                        }
                      >
                        {req.mandatory ? "Mandatory" : "Optional"}
                      </span>
                    </td>
                    {isEmployer && (
                      <td>
                        <button
                          className="btn-danger-sm"
                          onClick={() => handleDeleteRequirement(req.skill_id)}
                        >
                          ✕ Remove
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default JobDetails;
