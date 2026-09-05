import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { studentApi, jobApi, analysisApi, applicationApi } from "../services/api";

function Analysis() {
  const { user, isAdmin, isEmployer } = useAuth();

  const [students, setStudents] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState("");
  const [selectedJob, setSelectedJob] = useState("");

  const [loadingOptions, setLoadingOptions] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState("");
  const [applySuccess, setApplySuccess] = useState("");

  useEffect(() => {
    async function loadOptions() {
      try {
        const [studentsData, jobsData] = await Promise.allSettled([
          isAdmin ? studentApi.getStudents() : Promise.resolve([{ id: user?.id, name: user?.full_name || "My Profile", email: user?.email }]),
          jobApi.getJobs(),
        ]);

        if (studentsData.status === "fulfilled" && studentsData.value) {
          const sList = Array.isArray(studentsData.value) ? studentsData.value : studentsData.value.data || [];
          setStudents(sList);
          if (sList.length > 0) setSelectedStudent(String(sList[0].id));
        }

        if (jobsData.status === "fulfilled" && jobsData.value) {
          const jList = Array.isArray(jobsData.value) ? jobsData.value : jobsData.value.data || [];
          setJobs(jList);
          if (jList.length > 0) setSelectedJob(String(jList[0].id));
        }
      } catch (err) {
        setError("Could not load candidate and job options.");
      } finally {
        setLoadingOptions(false);
      }
    }
    loadOptions();
  }, [isAdmin, user]);

  const handleRunAnalysis = async () => {
    if (!selectedStudent || !selectedJob) {
      setError("Please select both a candidate and a target job.");
      return;
    }

    setAnalyzing(true);
    setError("");
    setApplySuccess("");

    try {
      const data = await analysisApi.triggerSkillGap(selectedStudent, selectedJob);
      setAnalysisResult(data);
    } catch (err) {
      setError(err.message || "Skill gap evaluation failed.");
      setAnalysisResult(null);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleApplyWithSnapshot = async () => {
    if (!selectedJob) return;
    try {
      await applicationApi.submitApplication(selectedJob);
      setApplySuccess("Application successfully recorded with this match percentage snapshot!");
    } catch (err) {
      setError(err.message || "Application submission failed.");
    }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1>Skill Gap Analysis</h1>
          <p>Evaluate proficiency alignment and compute weighted role match</p>
        </div>
      </div>

      {error && <div className="alert-error-banner">{error}</div>}
      {applySuccess && <div className="alert-success-banner">{applySuccess}</div>}

      {/* Analysis Selector Card */}
      <div className="dashboard-section">
        <h3>Select Evaluation Parameters</h3>
        <div className="analysis-selection-grid">
          <div className="form-group">
            <label>Candidate Profile:</label>
            <select
              value={selectedStudent}
              onChange={(e) => setSelectedStudent(e.target.value)}
              className="custom-select"
              disabled={loadingOptions || !isAdmin}
            >
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name || s.full_name} ({s.email})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Target Job Opening:</label>
            <select
              value={selectedJob}
              onChange={(e) => setSelectedJob(e.target.value)}
              className="custom-select"
              disabled={loadingOptions}
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} • {j.company_name}
                </option>
              ))}
            </select>
          </div>

          <button
            className="btn-primary"
            onClick={handleRunAnalysis}
            disabled={analyzing || loadingOptions}
            style={{ alignSelf: "flex-end", height: "46px" }}
          >
            {analyzing ? "Computing Gaps..." : "⚡ Execute Analysis"}
          </button>
        </div>
      </div>

      {/* Analysis Results Display */}
      {analysisResult && (
        <div className="analysis-results-wrapper" style={{ marginTop: "2rem" }}>
          <div className="analysis-score-banner">
            <div className="score-badge-circle">
              <span className="score-number">{analysisResult.overall_match_percentage}%</span>
              <span className="score-sub">Overall Match</span>
            </div>
            <div className="score-meta-text">
              <h3>Role Compatibility Evaluation</h3>
              <p>
                Algorithm Version: <strong>{analysisResult.algorithm_version || "v1.0"}</strong> •
                Evaluated: <strong>{new Date().toLocaleDateString()}</strong>
              </p>
              <p style={{ marginTop: "0.25rem", color: "#64748b" }}>
                Formula: Weighted proficiency ratio (Mandatory skills = 2.0x, Optional skills = 1.0x).
              </p>
            </div>
            {!isEmployer && (
              <button className="btn-primary" onClick={handleApplyWithSnapshot}>
                💼 Apply with this Snapshot
              </button>
            )}
          </div>

          {/* Granular Skill Gap Table */}
          <div className="dashboard-section" style={{ marginTop: "1.5rem" }}>
            <h3>Requirement Competency Breakdown</h3>
            <div className="table-responsive">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Skill</th>
                    <th>Importance</th>
                    <th>Required Level</th>
                    <th>Candidate Level</th>
                    <th>Gap Magnitude</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {analysisResult.skill_results?.map((res, i) => (
                    <tr key={i}>
                      <td>
                        <strong>{res.skill_name || `Skill #${res.skill_id}`}</strong>
                      </td>
                      <td>
                        <span className={res.mandatory ? "badge-req-mandatory" : "badge-req-optional"}>
                          {res.mandatory ? "Mandatory" : "Optional"}
                        </span>
                      </td>
                      <td>Level {res.required_proficiency}</td>
                      <td>Level {res.current_proficiency}</td>
                      <td>
                        {res.gap > 0 ? (
                          <span className="gap-pill">-{res.gap} Levels</span>
                        ) : (
                          <span className="match-pill">0 (Met)</span>
                        )}
                      </td>
                      <td>
                        <span className={res.matched ? "badge-status-matched" : "badge-status-gap"}>
                          {res.matched ? "✓ MATCHED" : "⚡ GAP"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Tailored Recommendations */}
          <div className="dashboard-section" style={{ marginTop: "1.5rem" }}>
            <h3>Prioritized Recommendations</h3>
            {analysisResult.recommendations && analysisResult.recommendations.length > 0 ? (
              <div className="recommendations-list">
                {analysisResult.recommendations.map((rec, i) => (
                  <div className="recommendation-item-card" key={i}>
                    <div className="rec-card-top">
                      <h4>{rec.skill_name || `Skill #${rec.skill_id}`}</h4>
                      <span className={`badge-priority-${(rec.priority || "MEDIUM").toLowerCase()}`}>
                        Priority: {String(rec.priority).toUpperCase()}
                      </span>
                    </div>
                    <p className="rec-reason">📌 {rec.reason}</p>
                    <p className="rec-suggestion">
                      {rec.suggested_action || "Advance your practical skills through targeted projects."}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-inline-note">
                🌟 Outstanding! All required competencies for this position are fully satisfied.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Analysis;
