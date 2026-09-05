import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { jobApi, studentApi, analysisApi } from "../services/api";
import { useAuth } from "../context/AuthContext";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";
import EmptyState from "../components/EmptyState";

function Recommendations() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();

  const [jobs, setJobs] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(searchParams.get("job_id") || "");
  const [selectedStudentId, setSelectedStudentId] = useState(searchParams.get("student_id") || "");

  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [metaLoading, setMetaLoading] = useState(true);
  const [error, setError] = useState("");

  const isStudent = user?.role === "student";

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setMetaLoading(true);
        const [jobsData] = await Promise.all([jobApi.getJobs()]);
        setJobs(Array.isArray(jobsData) ? jobsData : []);

        if (jobsData?.length > 0 && !selectedJobId) {
          setSelectedJobId(String(jobsData[0].id));
        }

        if (!isStudent) {
          try {
            const studentsData = await studentApi.getStudents();
            const sList = Array.isArray(studentsData) ? studentsData : [];
            setStudents(sList);
            if (sList.length > 0 && !selectedStudentId) {
              setSelectedStudentId(String(sList[0].id));
            }
          } catch (err) {
            console.warn("Could not list all students:", err);
          }
        } else {
          // If student, studentId is student's profile id or user id
          setSelectedStudentId(String(user?.student_id || user?.id || 1));
        }
      } catch (err) {
        setError(err.message || "Failed to load jobs or candidate data.");
      } finally {
        setMetaLoading(false);
      }
    };

    loadInitialData();
  }, [user]);

  const handleFetchRecommendations = async () => {
    if (!selectedJobId || !selectedStudentId) {
      setError("Please select both a candidate and a target job opening.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const data = await analysisApi.getRecommendations(selectedStudentId, selectedJobId);
      setRecommendations(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load recommendations:", err);
      setError(err.message || "Failed to generate recommendations.");
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedJobId && selectedStudentId && !metaLoading) {
      handleFetchRecommendations();
    }
  }, [selectedJobId, selectedStudentId, metaLoading]);

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Personalized Skill Recommendations</h1>
          <p className="page-subtitle">
            AI-driven, prioritized upskilling roadmaps calculated to maximize job match percentages and close critical skill gaps.
          </p>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {/* Filter Selection Header */}
      <div className="card shadow-sm p-4 mb-4">
        <div className="grid-2-col">
          {!isStudent && (
            <div className="form-group">
              <label className="form-label">Select Candidate</label>
              <select
                className="form-control"
                value={selectedStudentId}
                onChange={(e) => setSelectedStudentId(e.target.value)}
              >
                <option value="">-- Choose Candidate --</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.email}) - ID #{s.id}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Select Target Job Opening</label>
            <select
              className="form-control"
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
            >
              <option value="">-- Choose Target Job --</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} {j.company ? `at ${j.company}` : ""} (ID #{j.id})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-3 flex justify-end">
          <button
            className="btn btn-primary"
            onClick={handleFetchRecommendations}
            disabled={loading || !selectedJobId || !selectedStudentId}
          >
            {loading ? "Generating Roadmap..." : "Refresh Recommendations"}
          </button>
        </div>
      </div>

      {loading ? (
        <Loading />
      ) : recommendations.length === 0 ? (
        <EmptyState
          title="No Learning Recommendations Required"
          message="Candidate either fully meets all target requirements for this position, or no skill gaps have been recorded yet."
        />
      ) : (
        <div className="recommendation-grid">
          {recommendations.map((item, idx) => {
            const priorityLower = (item.priority || "medium").toLowerCase();
            const currentProf = item.current_proficiency ?? item.current ?? 0;
            const targetProf = item.target_proficiency ?? item.target ?? 5;
            const gap = targetProf - currentProf;

            return (
              <div key={item.id || item.skill_id || idx} className="recommendation-card">
                <div className="recommendation-header">
                  <div>
                    <h3 className="rec-skill-title">{item.skill_name || item.skill || `Skill #${item.skill_id}`}</h3>
                    <span className="rec-category-tag">{item.category || "Technical Skill"}</span>
                  </div>
                  <span className={`priority-badge priority-${priorityLower}`}>
                    {item.priority || "Normal"} Priority
                  </span>
                </div>

                <div className="rec-body mt-3">
                  <div className="proficiency-meter-container">
                    <div className="meter-labels">
                      <span>Current: <strong>{currentProf} / 5</strong></span>
                      <span>Target: <strong>{targetProf} / 5</strong></span>
                    </div>
                    <div className="progress-bar-bg">
                      <div
                        className="progress-bar-fill current-fill"
                        style={{ width: `${(currentProf / 5) * 100}%` }}
                        title={`Current: ${currentProf}/5`}
                      />
                      <div
                        className="progress-bar-fill target-fill"
                        style={{ width: `${(targetProf / 5) * 100}%` }}
                        title={`Target: ${targetProf}/5`}
                      />
                    </div>
                    <div className="text-right text-xs text-muted mt-1">
                      Deficit: <strong>+{gap > 0 ? gap : 0} levels required</strong>
                    </div>
                  </div>

                  <p className="rec-reason">
                    {item.reason ||
                      item.action_plan ||
                      (item.is_mandatory
                        ? "Mandatory requirement. Reaching the target level is essential for qualifying for this position."
                        : "Optional requirement. Elevating proficiency will significantly boost competitive score.")}
                  </p>

                  {item.action_plan && item.action_plan !== item.reason && (
                    <div className="rec-action-box">
                      <span className="rec-action-label">Action Plan:</span>
                      <p className="rec-action-text">{item.action_plan}</p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default Recommendations;
