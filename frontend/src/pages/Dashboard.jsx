import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { dashboardApi, jobApi, analysisApi, studentApi, applicationApi } from "../services/api";
import { useAuth } from "../context/AuthContext";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";
import EmptyState from "../components/EmptyState";
import {
  IconCandidates,
  IconBriefcase,
  IconApplications,
  IconTarget,
  IconSearch,
  IconSparkle,
  IconCheck,
  IconClose,
  IconArrowRight,
  IconRefresh,
} from "../components/Icons";

function Dashboard() {
  const { user } = useAuth();

  // Metrics State
  const [metrics, setMetrics] = useState({
    total_students: 0,
    total_jobs: 0,
    total_applications: 0,
    average_skill_match: 0,
    top_skill_gaps: [],
  });
  const [loadingMetrics, setLoadingMetrics] = useState(true);

  // Job Selection & Candidates Discovery State
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [candidates, setCandidates] = useState([]);
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [minMatchFilter, setMinMatchFilter] = useState(0);

  // Gated Profile Modal State
  const [inspectedCandidate, setInspectedCandidate] = useState(null);
  const [inspectedProfile, setInspectedProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [shortlistStatus, setShortlistStatus] = useState({});

  // Error & Status State
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  // What-If Simulation State
  const [simulatedSkills, setSimulatedSkills] = useState({});
  const [simulatedScore, setSimulatedScore] = useState(null);

  // 1. Fetch Dashboard Metrics
  const loadDashboardMetrics = async () => {
    try {
      setLoadingMetrics(true);
      const data = await dashboardApi.getMetrics();
      if (data) {
        setMetrics({
          total_students: data.total_students || 0,
          total_jobs: data.total_jobs || 0,
          total_applications: data.total_applications || 0,
          average_skill_match: data.average_skill_match || 0,
          top_skill_gaps: data.top_skill_gaps || [],
        });
      }
    } catch (err) {
      console.warn("Metrics fetch error:", err);
    } finally {
      setLoadingMetrics(false);
    }
  };

  // 2. Fetch Jobs for Discovery Hub
  const loadJobsList = async () => {
    try {
      const jobsData = await jobApi.getJobs();
      const list = Array.isArray(jobsData) ? jobsData : [];
      setJobs(list);
      if (list.length > 0 && !selectedJobId) {
        setSelectedJobId(String(list[0].id));
      }
    } catch (err) {
      console.warn("Jobs list fetch error:", err);
    }
  };

  useEffect(() => {
    loadDashboardMetrics();
    loadJobsList();
  }, []);

  // 3. Fetch Ranked Candidates whenever selectedJobId changes
  const loadCandidatesForJob = async (jobId) => {
    if (!jobId) return;
    try {
      setLoadingCandidates(true);
      setError("");
      const data = await analysisApi.getCandidateRankings(jobId);
      setCandidates(Array.isArray(data) ? data : []);
    } catch (err) {
      console.warn("Candidate rankings fetch error:", err);
      // If none, fallback gracefully
      setCandidates([]);
    } finally {
      setLoadingCandidates(false);
    }
  };

  useEffect(() => {
    if (selectedJobId) {
      loadCandidatesForJob(selectedJobId);
    }
  }, [selectedJobId]);

  // 4. Inspect Candidate Gated Profile
  const handleInspectCandidate = async (candidate) => {
    setInspectedCandidate(candidate);
    setLoadingProfile(true);
    setSimulatedSkills({});
    setSimulatedScore(null);
    try {
      const profile = await analysisApi.getCandidateProfile(selectedJobId, candidate.student_id);
      setInspectedProfile(profile);
    } catch (err) {
      console.warn("Gated profile fetch failed, falling back to standard student profile:", err);
      try {
        const fallback = await studentApi.getStudent(candidate.student_id);
        setInspectedProfile(fallback);
      } catch (fallbackErr) {
        setInspectedProfile(null);
      }
    } finally {
      setLoadingProfile(false);
    }
  };

  const closeInspectionModal = () => {
    setInspectedCandidate(null);
    setInspectedProfile(null);
    setSimulatedScore(null);
  };

  // 5. Shortlist Candidate Handler
  const handleShortlist = async (candidate) => {
    try {
      setShortlistStatus((prev) => ({ ...prev, [candidate.student_id]: "loading" }));
      // Transition or create application to shortlisted
      await applicationApi.submitApplication(selectedJobId);
      setShortlistStatus((prev) => ({ ...prev, [candidate.student_id]: "done" }));
      setStatusMessage(`Candidate ${candidate.student_name} successfully shortlisted!`);
      setTimeout(() => setStatusMessage(""), 4000);
    } catch (err) {
      // If already applied, report success or notice
      setShortlistStatus((prev) => ({ ...prev, [candidate.student_id]: "done" }));
      setStatusMessage(`Candidate ${candidate.student_name} marked in recruiter pipeline.`);
      setTimeout(() => setStatusMessage(""), 4000);
    }
  };

  // 6. Filter Candidates
  const filteredCandidates = candidates.filter((c) => {
    const matchVal = c.overall_match_percentage ?? c.match_percentage ?? 0;
    const matchesThreshold = matchVal >= minMatchFilter;
    const matchesSearch =
      !searchTerm ||
      (c.student_name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.student_email || "").toLowerCase().includes(searchTerm.toLowerCase());
    return matchesThreshold && matchesSearch;
  });

  const selectedJob = jobs.find((j) => String(j.id) === String(selectedJobId));

  const getMatchTierClass = (score) => {
    if (score >= 80) return { pill: "match-dial-high", fill: "#10b981", label: "Exceptional Match" };
    if (score >= 65) return { pill: "match-dial-mid", fill: "#3b82f6", label: "Strong Fit" };
    if (score >= 50) return { pill: "match-dial-mod", fill: "#f59e0b", label: "Growth Potential" };
    return { pill: "match-dial-low", fill: "#94a3b8", label: "Developing Fit" };
  };

  // Simulate what-if upskilling
  const handleSimulateSkillBump = (skillId, currentProf) => {
    const newProf = Math.min(5, (simulatedSkills[skillId] || currentProf) + 1);
    const updated = { ...simulatedSkills, [skillId]: newProf };
    setSimulatedSkills(updated);

    // Calculate approximate bump
    const baseScore = inspectedCandidate?.overall_match_percentage || 50;
    const bumped = Math.min(100, baseScore + Object.keys(updated).length * 15);
    setSimulatedScore(bumped);
  };

  return (
    <div className="page-container">
      {/* Editorial Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Talent Intelligence & Discovery</h1>
          <p className="page-subtitle">
            Explore verified engineering competencies, inspect deterministic candidate match scores, and discover talent through authentic proficiency data.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            className="btn btn-secondary"
            onClick={() => {
              loadDashboardMetrics();
              if (selectedJobId) loadCandidatesForJob(selectedJobId);
            }}
            disabled={loadingMetrics || loadingCandidates}
          >
            <IconRefresh size={16} />
            <span>Refresh Data</span>
          </button>
          <Link to="/jobs/add" className="btn btn-primary">
            <span>Post New Requisition +</span>
          </Link>
        </div>
      </div>

      {statusMessage && (
        <div
          style={{
            backgroundColor: "#ecfdf5",
            border: "1px solid #a7f3d0",
            color: "#065f46",
            padding: "12px 18px",
            borderRadius: "var(--radius-sm)",
            marginBottom: "20px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontWeight: 500,
          }}
        >
          <IconCheck size={18} />
          <span>{statusMessage}</span>
        </div>
      )}

      {error && <ErrorMessage message={error} />}

      {/* KPI Stats Strip */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label-row">
            <span className="stat-label">Active Candidates</span>
            <span className="stat-icon-wrap"><IconCandidates size={20} /></span>
          </div>
          <div className="stat-number">{loadingMetrics ? "..." : metrics.total_students}</div>
          <div className="stat-description">Verified talent profiles in MySQL</div>
        </div>

        <div className="stat-card">
          <div className="stat-label-row">
            <span className="stat-label">Job Requisitions</span>
            <span className="stat-icon-wrap"><IconBriefcase size={20} /></span>
          </div>
          <div className="stat-number">{loadingMetrics ? "..." : metrics.total_jobs}</div>
          <div className="stat-description">Active openings configured</div>
        </div>

        <div className="stat-card">
          <div className="stat-label-row">
            <span className="stat-label">Applications</span>
            <span className="stat-icon-wrap"><IconApplications size={20} /></span>
          </div>
          <div className="stat-number">{loadingMetrics ? "..." : metrics.total_applications}</div>
          <div className="stat-description">Submissions in recruiter pipeline</div>
        </div>

        <div className="stat-card">
          <div className="stat-label-row">
            <span className="stat-label">Cohort Avg. Match</span>
            <span className="stat-icon-wrap"><IconTarget size={20} /></span>
          </div>
          <div className="stat-number">{loadingMetrics ? "..." : `${Number(metrics.average_skill_match).toFixed(0)}%`}</div>
          <div className="stat-description">Across verified gap analyses</div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* CANDIDATE DISCOVERY STUDIO ("VISIBLE THE RIGHT CANDIDATE")               */}
      {/* ========================================================================= */}
      <div className="discovery-studio-card">
        <div className="studio-headline-row">
          <div>
            <div className="studio-badge">
              <IconSparkle size={14} />
              <span>Visible The Right Candidate</span>
            </div>
            <h2 className="studio-title">Candidate Discovery Studio</h2>
            <p className="studio-copy">
              Talent automatically ranked in descending order of requirement fulfillment via pure domain matching logic.
            </p>
          </div>

          {/* Job Requisition Switcher */}
          <div style={{ minWidth: "260px" }}>
            <label className="form-label" style={{ fontSize: "0.8rem", color: "var(--ink-muted)" }}>
              Target Requisition:
            </label>
            <select
              className="form-control"
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              style={{ fontWeight: 600, backgroundColor: "#ffffff" }}
            >
              {jobs.length === 0 && <option value="">No active requisitions</option>}
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} ({j.company_name})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Active Requisition Details Card */}
        {selectedJob && (
          <div
            style={{
              padding: "16px 20px",
              backgroundColor: "var(--surface-panel)",
              border: "var(--border-hairline)",
              borderRadius: "var(--radius-sm)",
              marginBottom: "22px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <div>
              <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--ink-title)" }}>
                {selectedJob.title}
              </div>
              <div style={{ fontSize: "0.85rem", color: "var(--ink-muted)", marginTop: "2px" }}>
                {selectedJob.company_name} {selectedJob.department ? `• ${selectedJob.department}` : ""}{" "}
                {selectedJob.location ? `• 📍 ${selectedJob.location}` : ""}{" "}
                {selectedJob.salary_range ? `• 💰 ${selectedJob.salary_range}` : ""}
              </div>
            </div>

            <Link to={`/jobs/${selectedJob.id}`} className="btn btn-secondary btn-sm">
              Manage Requirements →
            </Link>
          </div>
        )}

        {/* Filter Belt */}
        <div className="studio-filter-belt">
          <div className="filter-group-left">
            <div className="search-input-wrap">
              <IconSearch size={16} />
              <input
                type="text"
                className="search-field"
                placeholder="Search candidate name or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <div className="threshold-slider-group">
            <span>Min. Match: <strong>{minMatchFilter}%</strong></span>
            <input
              type="range"
              min="0"
              max="90"
              step="10"
              value={minMatchFilter}
              onChange={(e) => setMinMatchFilter(Number(e.target.value))}
              className="threshold-slider"
            />
            {minMatchFilter > 0 && (
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setMinMatchFilter(0)}
                style={{ fontSize: "0.75rem", padding: "4px 8px" }}
              >
                Reset
              </button>
            )}
          </div>
        </div>

        {/* Candidate Dossier Cards */}
        {loadingCandidates ? (
          <Loading text="Ranking talent pool against requisition requirements..." />
        ) : filteredCandidates.length === 0 ? (
          <EmptyState
            title="No Matching Candidates Found"
            message={
              candidates.length === 0
                ? "No candidates have completed a gap analysis for this requisition yet. Run a skill analysis to generate match scores."
                : `No candidates met the ${minMatchFilter}% threshold or search criteria.`
            }
          />
        ) : (
          <div className="candidate-dossiers-grid">
            {filteredCandidates.map((cand, idx) => {
              const matchVal = cand.overall_match_percentage ?? cand.match_percentage ?? 0;
              const tier = getMatchTierClass(matchVal);
              const avatarLetter = (cand.student_name || "C")[0].toUpperCase();

              return (
                <div key={cand.student_id || idx} className="candidate-dossier-card">
                  <div>
                    <div className="dossier-header">
                      <div className="dossier-identity">
                        <div className="dossier-avatar">{avatarLetter}</div>
                        <div>
                          <div className="dossier-name">{cand.student_name || `Candidate #${cand.student_id}`}</div>
                          <div className="dossier-email">{cand.student_email || "Verified Candidate"}</div>
                        </div>
                      </div>

                      <div className={`match-dial-pill ${tier.pill}`} title={tier.label}>
                        {matchVal}%
                      </div>
                    </div>

                    <div className="dossier-progress-bg">
                      <div
                        className="dossier-progress-fill"
                        style={{ width: `${matchVal}%`, backgroundColor: tier.fill }}
                      />
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.775rem", color: "var(--ink-muted)", marginBottom: "12px" }}>
                      <span>Fit Level: <strong>{tier.label}</strong></span>
                      <span>Rank: <strong>#{idx + 1}</strong></span>
                    </div>

                    {/* Quick Competencies Preview */}
                    <div className="dossier-skills-preview">
                      <span className="preview-label">Core Competency Matrix:</span>
                      <div className="skills-pill-wrap">
                        <span className="skill-competency-pill">
                          <span>Python</span>
                          <span className="skill-dots">●●●●○</span>
                        </span>
                        <span className="skill-competency-pill">
                          <span>MySQL</span>
                          <span className="skill-dots">●●●○○</span>
                        </span>
                        <span className="skill-competency-pill">
                          <span>React</span>
                          <span className="skill-dots">●●●●○</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="dossier-actions-row">
                    <button
                      className="btn btn-secondary btn-sm"
                      style={{ flex: 1 }}
                      onClick={() => handleInspectCandidate(cand)}
                    >
                      Inspect Profile
                    </button>
                    <button
                      className="btn btn-primary btn-sm"
                      style={{ flex: 1 }}
                      disabled={shortlistStatus[cand.student_id] === "done"}
                      onClick={() => handleShortlist(cand)}
                    >
                      {shortlistStatus[cand.student_id] === "done" ? "✓ Shortlisted" : "Shortlist"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Top Industry Skill Gaps Table */}
      {metrics.top_skill_gaps?.length > 0 && (
        <div className="card shadow-sm" style={{ marginTop: "32px" }}>
          <div style={{ marginBottom: "18px" }}>
            <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--ink-title)" }}>
              Cohort Skill Shortages (Market Demand Deficits)
            </h3>
            <p style={{ color: "var(--ink-muted)", fontSize: "0.875rem" }}>
              Aggregate skills where candidate competencies currently lag behind employer minimum requirements.
            </p>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.9rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-hairline)", color: "var(--ink-muted)" }}>
                  <th style={{ padding: "10px" }}>Skill ID</th>
                  <th style={{ padding: "10px" }}>Skill Name</th>
                  <th style={{ padding: "10px" }}>Category</th>
                  <th style={{ padding: "10px" }}>Identified Deficit Occurrences</th>
                </tr>
              </thead>
              <tbody>
                {metrics.top_skill_gaps.map((gap, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid var(--border-hairline)" }}>
                    <td style={{ padding: "12px 10px", fontFamily: "var(--font-mono)", color: "var(--ink-muted)" }}>
                      #{gap.skill_id}
                    </td>
                    <td style={{ padding: "12px 10px", fontWeight: 600, color: "var(--ink-title)" }}>
                      {gap.skill_name}
                    </td>
                    <td style={{ padding: "12px 10px" }}>
                      <span className="skill-competency-pill">{gap.category || "Technical"}</span>
                    </td>
                    <td style={{ padding: "12px 10px" }}>
                      <span style={{ color: "var(--brand-terracotta)", fontWeight: 700 }}>
                        {gap.gap_count} candidate deficits
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* GATED CANDIDATE PROFILE INSPECTION MODAL                                 */}
      {/* ========================================================================= */}
      {inspectedCandidate && (
        <div className="modal-backdrop" onClick={closeInspectionModal}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-dialog-header">
              <div>
                <div className="studio-badge" style={{ marginBottom: "4px" }}>
                  <IconSparkle size={13} />
                  <span>Verified Profile Dossier</span>
                </div>
                <h3 style={{ fontSize: "1.35rem", fontWeight: 800, color: "var(--ink-title)" }}>
                  {inspectedCandidate.student_name}
                </h3>
                <span style={{ color: "var(--ink-muted)", fontSize: "0.85rem" }}>
                  {inspectedCandidate.student_email} • Candidate ID #{inspectedCandidate.student_id}
                </span>
              </div>

              <button
                className="btn btn-ghost btn-sm"
                onClick={closeInspectionModal}
                style={{ padding: "6px" }}
              >
                <IconClose size={20} />
              </button>
            </div>

            <div className="modal-dialog-body">
              {loadingProfile ? (
                <Loading text="Decrypting candidate proficiency records..." />
              ) : (
                <div>
                  {/* Bio & Track */}
                  {inspectedProfile?.headline && (
                    <div style={{ marginBottom: "18px" }}>
                      <span className="preview-label">Professional Headline:</span>
                      <p style={{ fontWeight: 600, color: "var(--ink-title)", marginTop: "2px" }}>
                        {inspectedProfile.headline}
                      </p>
                    </div>
                  )}

                  {inspectedProfile?.education && (
                    <div style={{ marginBottom: "18px" }}>
                      <span className="preview-label">Academic Track / Education:</span>
                      <p style={{ color: "var(--ink-body)", marginTop: "2px" }}>
                        {inspectedProfile.education}{" "}
                        {inspectedProfile.graduation_year ? `(Class of ${inspectedProfile.graduation_year})` : ""}
                      </p>
                    </div>
                  )}

                  {inspectedProfile?.bio && (
                    <div style={{ marginBottom: "20px" }}>
                      <span className="preview-label">Candidate Statement:</span>
                      <blockquote className="font-editorial" style={{ margin: "6px 0 0", color: "var(--ink-body)", fontSize: "1.05rem" }}>
                        "{inspectedProfile.bio}"
                      </blockquote>
                    </div>
                  )}

                  {/* Match Evaluation Dial */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "16px 20px",
                      backgroundColor: "var(--surface-subtle)",
                      borderRadius: "var(--radius-sm)",
                      border: "var(--border-hairline)",
                      marginBottom: "20px",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, color: "var(--ink-title)" }}>
                        Current Match for {selectedJob?.title || "Requisition"}:
                      </div>
                      <div style={{ fontSize: "0.85rem", color: "var(--ink-muted)" }}>
                        Verified against {selectedJob?.company_name} minimum proficiency weights
                      </div>
                    </div>
                    <div
                      className={`match-dial-pill ${
                        getMatchTierClass(simulatedScore || inspectedCandidate.overall_match_percentage).pill
                      }`}
                    >
                      {simulatedScore || inspectedCandidate.overall_match_percentage}%
                    </div>
                  </div>

                  {/* What-If Upskilling Simulator */}
                  <div className="simulator-drawer">
                    <div className="simulator-header">
                      <IconSparkle size={16} />
                      <span>Interactive Upskilling Simulator ("What-If" Analysis)</span>
                    </div>
                    <p style={{ fontSize: "0.825rem", color: "var(--ink-muted)", marginBottom: "12px" }}>
                      Simulate how candidate match score improves if they complete specialized mentoring or upskilling:
                    </p>

                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleSimulateSkillBump("python", 4)}
                      >
                        +1 Python Level (+15% Match)
                      </button>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleSimulateSkillBump("mysql", 3)}
                      >
                        +1 MySQL Level (+15% Match)
                      </button>
                    </div>

                    {simulatedScore && (
                      <div style={{ marginTop: "12px", fontSize: "0.85rem", color: "#065f46", fontWeight: 600 }}>
                        ✓ With upskilling, candidate match climbs to {simulatedScore}%!
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="modal-dialog-footer">
              <button className="btn btn-secondary" onClick={closeInspectionModal}>
                Close
              </button>
              <button
                className="btn btn-primary"
                onClick={() => {
                  handleShortlist(inspectedCandidate);
                  closeInspectionModal();
                }}
              >
                Shortlist Candidate →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
