import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { studentApi } from "../services/api";

function Students() {
  const { user, isAdmin, isEmployer } = useAuth();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchStudents() {
      if (isEmployer) {
        setLoading(false);
        return;
      }
      try {
        if (isAdmin) {
          const res = await studentApi.getStudents();
          const list = Array.isArray(res) ? res : res.data || [];
          setStudents(list);
        } else {
          // For student role, load own student profile
          try {
            const profile = await studentApi.getStudent(user?.id);
            if (profile) setStudents([profile]);
          } catch {
            setStudents([
              {
                id: user?.id,
                name: user?.full_name || "Student User",
                email: user?.email,
                headline: "Candidate Profile",
              },
            ]);
          }
        }
      } catch (err) {
        setError(err.message || "Could not load students directory.");
      } finally {
        setLoading(false);
      }
    }
    fetchStudents();
  }, [isAdmin, isEmployer, user]);

  if (isEmployer) {
    return (
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h1>Candidate Discovery & Search</h1>
            <p>Filter candidates by technical skills against your job requisitions</p>
          </div>
        </div>

        <div className="dashboard-section" style={{ textAlign: "center", padding: "48px 24px" }}>
          <div style={{ fontSize: "3rem", marginBottom: "16px" }}>🔍</div>
          <h2>Search Candidates by Skills</h2>
          <p style={{ maxWidth: "560px", margin: "8px auto 24px auto", color: "var(--ink-muted)", lineHeight: 1.6 }}>
            Employers can match, filter, and inspect verified candidate proficiencies directly against active job requisitions in the Candidate Discovery Studio.
          </p>
          <Link to="/dashboard" className="btn-primary" style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
            Open Candidate Discovery Studio →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1>{isAdmin ? "Talent Pool Directory" : "My Candidate Profile"}</h1>
          <p>{isAdmin ? "View and manage registered candidates" : "Manage your verified skills and profile"}</p>
        </div>

        {isAdmin && (
          <Link to="/students/add" className="btn-primary">
            + Add Student
          </Link>
        )}
      </div>

      {error && <div className="alert-error-banner">{error}</div>}

      {loading ? (
        <div className="loading-state-card">
          <div className="spinner"></div>
          <p>Loading candidate data from MySQL...</p>
        </div>
      ) : students.length === 0 ? (
        <div className="empty-talent-card">
          <div className="empty-icon">🎓</div>
          <h3>No students found</h3>
          <p>Candidates will appear here once registered.</p>
        </div>
      ) : (
        <div className="table-responsive">
          <table className="custom-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Candidate Name</th>
                <th>Email</th>
                <th>Headline</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                <tr key={student.id}>
                  <td>#{student.id}</td>
                  <td>
                    <strong>{student.name || student.full_name || "Candidate"}</strong>
                  </td>
                  <td>{student.email}</td>
                  <td>{student.headline || "Seeking Opportunities"}</td>
                  <td>
                    <Link to={`/students/${student.id}`} className="btn-outline-sm">
                      Inspect Profile & Skills →
                    </Link>
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

export default Students;
