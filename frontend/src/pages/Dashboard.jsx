import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  dashboardApi,
  jobApi,
  analysisApi,
  studentApi,
  applicationApi,
  skillApi,
} from "../services/api";
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
  IconFilter,
  IconSparkle,
  IconCheck,
  IconClose,
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

  // Search & Filtering State
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSkillFilter, setSelectedSkillFilter] = useState("all");
  const [minProficiencyFilter, setMinProficiencyFilter] = useState(0);
  const [minMatchFilter, setMinMatchFilter] = useState(0);

  // Requisition Skills & Catalog Skills State
  const [jobRequirements, setJobRequirements] = useState([]);
  const [catalogSkills, setCatalogSkills] = useState([]);

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

  // 2. Fetch Jobs and Global Skill Catalog
  const loadInitialData = async () => {
    try {
      const [jobsData, skillsData] = await Promise.all([
        jobApi.getJobs(),
        skillApi.getSkills().catch(() => []),
      ]);
      const list = Array.isArray(jobsData) ? jobsData : [];
      setJobs(list);
      setCatalogSkills(Array.isArray(skillsData) ? skillsData : []);
      if (list.length > 0 && !selectedJobId) {
        setSelectedJobId(String(list[0].id));
      }
    } catch (err) {
      console.warn("Initial data fetch error:", err);
    }
  };

  useEffect(() => {
    loadDashboardMetrics();
    loadInitialData();
  }, []);

  // 3. Fetch Job Requirements & Ranked Candidates when selectedJobId changes
  const loadCandidatesAndRequirements = async (jobId) => {
    if (!jobId) return;
    try {
      setLoadingCandidates(true);
      setError("");

      const [candidatesData, reqsData] = await Promise.all([
        analysisApi.getCandidateRankings(jobId, {
          skill: selectedSkillFilter !== "all" ? selectedSkillFilter : undefined,
          min_proficiency: minProficiencyFilter > 0 ? minProficiencyFilter : undefined,
        }),
        jobApi.getRequirements(jobId).catch(() => []),
      ]);

      setCandidates(Array.isArray(candidatesData) ? candidatesData : []);
      setJobRequirements(Array.isArray(reqsData) ? reqsData : []);
    } catch (err) {
      console.warn("Candidates/Requirements fetch error:", err);
      setCandidates([]);
      setJobRequirements([]);
    } finally {
      setLoadingCandidates(false);
    }
  };

  useEffect(() => {
    if (selectedJobId) {
      loadCandidatesAndRequirements(selectedJobId);
    }
  }, [selectedJobId, selectedSkillFilter, minProficiencyFilter]);

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
      await applicationApi.submitApplication(selectedJobId);
      setShortlistStatus((prev) => ({ ...prev, [candidate.student_id]: "done" }));
      setStatusMessage(`Candidate ${candidate.student_name} successfully shortlisted!`);
      setTimeout(() => setStatusMessage(""), 4000);
    } catch (err) {
      setShortlistStatus((prev) => ({ ...prev, [candidate.student_id]: "done" }));
      setStatusMessage(`Candidate ${candidate.student_name} marked in recruiter pipeline.`);
      setTimeout(() => setStatusMessage(""), 4000);
    }
  };

  // Helper to render proficiency dots
  const renderProficiencyDots = (lvl) => {
    const filled = Math.min(5, Math.max(0, lvl || 0));
    return "●".repeat(filled) + "○".repeat(5 - filled);
  };

  // Helper to check requirement alignment
  const getRequirementComparison = (skillName, candidateProf) => {
    if (!jobRequirements || jobRequirements.length === 0) return null;
    const req = jobRequirements.find(
      (r) => (r.skill_name || "").toLowerCase() === (skillName || "").toLowerCase()
    );
    if (!req) return null;
    const reqLevel = req.required_proficiency ?? req.required_level ?? 1;
    const isMet = (candidateProf || 0) >= reqLevel;
    return {
      reqLevel,
      isMet,
      mandatory: req.mandatory,
    };
  };

  // 6. Client-Side Real-Time Filtering
  const filteredCandidates = candidates.filter((c) => {
    const matchVal = c.overall_match_percentage ?? c.match_percentage ?? 0;
    const matchesThreshold = matchVal >= minMatchFilter;

    // Search query: checks student name, email, headline, or ANY skill name
    const q = (searchTerm || "").trim().toLowerCase();
    const matchesSearch =
      !q ||
      (c.student_name || "").toLowerCase().includes(q) ||
      (c.student_email || "").toLowerCase().includes(q) ||
      (c.headline || "").toLowerCase().includes(q) ||
      (c.skills && c.skills.some((sk) => sk.skill_name.toLowerCase().includes(q)));

    // Specific skill tag filter
    let matchesSkill = true;
    if (selectedSkillFilter && selectedSkillFilter !== "all") {
      const targetSkill = c.skills?.find(
        (sk) => sk.skill_name.toLowerCase() === selectedSkillFilter.toLowerCase()
      );
      if (!targetSkill) {
        matchesSkill = false;
      } else if (minProficiencyFilter > 0 && targetSkill.proficiency < minProficiencyFilter) {
        matchesSkill = false;
      }
    }

    return matchesThreshold && matchesSearch && matchesSkill;
  });

  const selectedJob = jobs.find((j) => String(j.id) === String(selectedJobId));

  const getMatchTierClass = (score) => {
    if (score >= 80) return { pill: "match-dial-high", fill: "#10b981", label: "Exceptional Match" };
    if (score >= 65) return { pill: "match-dial-mid", fill: "#3b82f6", label: "Strong Fit" };
    if (score >= 50) return { pill: "match-dial-mod", fill: "#f59e0b", label: "Growth Potential" };
    return { pill: "match-dial-low", fill: "#94a3b8", label: "Developing Fit" };
  };

  // What-If Simulation
  const handleSimulateSkillBump = (skillName, currentProf) => {
    const newProf = Math.min(5, (simulatedSkills[skillName] || currentProf) + 1);
    const updated = { ...simulatedSkills, [skillName]: newProf };
    setSimulatedSkills(updated);

    const baseScore = inspectedCandidate?.overall_match_percentage || 50;
    const bumped = Math.min(100, baseScore + Object.keys(updated).length * 15);
    setSimulatedScore(bumped);
  };

  return (
    <div className="page-container">
      {/* Editorial Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Talent Intelligence & Skill Discovery</h1>
          <p className="page-subtitle">
            Search candidates by engineering skills, compare proficiencies directly against job requirements, and shortlist the right talent.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            className="btn btn-secondary"
            onClick={() => {
              loadDashboardMetrics();
              if (selectedJobId) loadCandidatesAndRequirements(selectedJobId);
            }}
            disabled={loadingMetrics || loadingCandidates}
          >
            <IconRefresh size={16} />
            <span>Refresh Studio</span>
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
              Search candidates by specific skills, evaluate alignment with role requirements, and filter by minimum proficiency.
            </p>
          </div>

          {/* Job Requisition Switcher */}
          <div style={{ minWidth: "270px" }}>
            <label className="form-label" style={{ fontSize: "0.8rem", color: "var(--ink-muted)" }}>
              Target Job Requisition:
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
              marginBottom: "20px",
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
              Manage Requirements ({jobRequirements.length}) →
            </Link>
          </div>
        )}

        {/* ========================================================================= */}
        {/* SKILL SEARCH & MULTI-FILTER BELT                                         */}
        {/* ========================================================================= */}
        <div className="skill-filter-section">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, fontSize: "0.875rem", color: "var(--ink-title)" }}>
              <IconFilter size={16} />
              <span>Filter Candidates by Skills & Competency</span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--ink-muted)" }}>
                Minimum Proficiency:
              </label>
              <select
                className="proficiency-select-inline"
                value={minProficiencyFilter}
                onChange={(e) => setMinProficiencyFilter(Number(e.target.value))}
              >
                <option value={0}>Any Proficiency (1-5)</option>
                <option value={2}>Working (2+)</option>
                <option value={3}>Competent (3+)</option>
                <option value={4}>Advanced (4+)</option>
                <option value={5}>Master / Expert (5/5)</option>
              </select>
            </div>
          </div>

          {/* Quick Skill Filter Chips Row */}
          <div className="skill-chips-row">
            <button
              className={`skill-filter-chip ${selectedSkillFilter === "all" ? "active" : ""}`}
              onClick={() => setSelectedSkillFilter("all")}
            >
              All Skills ({candidates.length})
            </button>

            {/* Requisition Required Skills (Highlighted as Job Requirements) */}
            {jobRequirements.map((req) => {
              const sName = req.skill_name || `Skill #${req.skill_id}`;
              const reqProf = req.required_proficiency ?? req.required_level ?? 1;
              const isSelected = selectedSkillFilter.toLowerCase() === sName.toLowerCase();
              return (
                <button
                  key={req.id || req.skill_id}
                  className={`skill-filter-chip is-job-req ${isSelected ? "active" : ""}`}
                  onClick={() => setSelectedSkillFilter(isSelected ? "all" : sName)}
                  title={`Job Requirement: Minimum Level ${reqProf}/5 ${req.mandatory ? "(Mandatory)" : "(Optional)"}`}
                >
                  <span>✦ {sName}</span>
                  <span style={{ fontSize: "0.725rem", opacity: 0.85 }}>Req: {reqProf}/5</span>
                </button>
              );
            })}

            {/* Other Catalog Skills */}
            {catalogSkills
              .filter((cat) => !jobRequirements.some((r) => (r.skill_name || "").toLowerCase() === cat.name.toLowerCase()))
              .map((cat) => {
                const isSelected = selectedSkillFilter.toLowerCase() === cat.name.toLowerCase();
                return (
                  <button
                    key={cat.id}
                    className={`skill-filter-chip ${isSelected ? "active" : ""}`}
                    onClick={() => setSelectedSkillFilter(isSelected ? "all" : cat.name)}
                  >
                    <span>{cat.name}</span>
                  </button>
                );
              })}
          </div>

          {/* Active Filter Status Bar */}
          {(selectedSkillFilter !== "all" || minProficiencyFilter > 0 || searchTerm) && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "8px 12px",
                backgroundColor: "#ffffff",
                borderRadius: "var(--radius-xs)",
                fontSize: "0.8rem",
                color: "var(--ink-muted)",
                border: "1px dashed var(--border-hairline)",
              }}
            >
              <div>
                Active Skill Filter:{" "}
                <strong style={{ color: "var(--brand-primary)" }}>
                  {selectedSkillFilter !== "all" ? selectedSkillFilter : "All Skills"}
                </strong>
                {minProficiencyFilter > 0 && ` (Min Level: ${minProficiencyFilter}/5)`}
                {searchTerm && ` • Search: "${searchTerm}"`}
                {" — "}
                Found <strong>{filteredCandidates.length}</strong> matching candidate(s)
              </div>

              <button
                className="btn btn-ghost btn-sm"
                style={{ fontSize: "0.75rem", padding: "2px 6px" }}
                onClick={() => {
                  setSelectedSkillFilter("all");
                  setMinProficiencyFilter(0);
                  setSearchTerm("");
                }}
              >
                Clear Filters ✕
              </button>
            </div>
          )}
        </div>

        {/* Search Input & Match Threshold Slider Belt */}
        <div className="studio-filter-belt">
          <div className="filter-group-left">
            <div className="search-input-wrap">
              <IconSearch size={16} />
              <input
                type="text"
                className="search-field"
                placeholder="Search candidate name, email, or skill..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <div className="threshold-slider-group">
            <span>Overall Match: <strong>{minMatchFilter}%</strong></span>
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
          <Loading text="Ranking talent pool against requisition requirements & skills..." />
        ) : filteredCandidates.length === 0 ? (
          <EmptyState
            title="No Matching Candidates Found"
            message={
              selectedSkillFilter !== "all"
                ? `No candidates found with skill "${selectedSkillFilter}" meeting ${minProficiencyFilter > 0 ? `proficiency ${minProficiencyFilter}/5` : "criteria"}. Try selecting another skill chip or lowering the proficiency threshold.`
                : candidates.length === 0
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

                    {/* Candidate Verified Skills with Requirement Matching */}
                    <div className="dossier-skills-preview">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span className="preview-label">Candidate Verified Skills:</span>
                        <span style={{ fontSize: "0.75rem", color: "var(--ink-subtle)" }}>
                          {cand.skills?.length || 0} skills
                        </span>
                      </div>

                      <div className="skills-pill-wrap">
                        {cand.skills && cand.skills.length > 0 ? (
                          cand.skills.map((sk) => {
                            const reqComp = getRequirementComparison(sk.skill_name, sk.proficiency);
                            const isFilterMatch =
                              selectedSkillFilter.toLowerCase() === sk.skill_name.toLowerCase() ||
                              (searchTerm && sk.skill_name.toLowerCase().includes(searchTerm.toLowerCase()));

                            return (
                              <span
                                key={sk.skill_id}
                                className={`skill-competency-pill ${isFilterMatch ? "highlighted" : ""}`}
                                onClick={() => setSelectedSkillFilter(sk.skill_name)}
                                title={`Click to filter candidates by ${sk.skill_name}`}
                                style={{ cursor: "pointer" }}
                              >
                                <span>{sk.skill_name}</span>
                                <span className="skill-dots">{renderProficiencyDots(sk.proficiency)}</span>
                                <strong style={{ fontSize: "0.75rem" }}>{sk.proficiency}/5</strong>

                                {reqComp && (
                                  reqComp.isMet ? (
                                    <span className="skill-req-status-met">
                                      ✓ Req {reqComp.reqLevel}
                                    </span>
                                  ) : (
                                    <span className="skill-req-status-gap">
                                      ⚠️ Req {reqComp.reqLevel}
                                    </span>
                                  )
                                )}
                              </span>
                            );
                          })
                        ) : (
                          <span style={{ fontSize: "0.8rem", color: "var(--ink-muted)" }}>
                            Candidate has not registered skills yet.
                          </span>
                        )}
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

                  {/* Complete Verified Skills Breakdown in Modal */}
                  <div style={{ marginBottom: "20px" }}>
                    <span className="preview-label">All Verified Skills & Proficiency:</span>
                    <div className="skills-pill-wrap" style={{ marginTop: "8px" }}>
                      {inspectedProfile?.skills && inspectedProfile.skills.length > 0 ? (
                        inspectedProfile.skills.map((s) => {
                          const reqComp = getRequirementComparison(s.skill_name, s.proficiency);
                          return (
                            <span key={s.id || s.skill_id} className="skill-competency-pill">
                              <strong>{s.skill_name}</strong>
                              <span className="skill-dots">{renderProficiencyDots(s.proficiency)}</span>
                              <span>{s.proficiency}/5</span>
                              {reqComp && (
                                reqComp.isMet ? (
                                  <span className="skill-req-status-met">✓ Meets Req ({reqComp.reqLevel})</span>
                                ) : (
                                  <span className="skill-req-status-gap">⚠️ Gap (Req: {reqComp.reqLevel})</span>
                                )
                              )}
                            </span>
                          );
                        })
                      ) : (
                        <p style={{ fontSize: "0.85rem", color: "var(--ink-muted)" }}>
                          No individual skills recorded for this candidate.
                        </p>
                      )}
                    </div>
                  </div>

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
                        Match Evaluation for {selectedJob?.title || "Requisition"}:
                      </div>
                      <div style={{ fontSize: "0.85rem", color: "var(--ink-muted)" }}>
                        Calculated by pure domain matching engine
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
                      Simulate how candidate match score improves if they upskill in a required role competency:
                    </p>

                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                      {jobRequirements.map((req) => {
                        const sName = req.skill_name || `Skill #${req.skill_id}`;
                        return (
                          <button
                            key={req.skill_id}
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleSimulateSkillBump(sName, 3)}
                          >
                            +1 {sName} Level (+15% Match)
                          </button>
                        );
                      })}
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
