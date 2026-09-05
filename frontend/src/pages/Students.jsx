import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { studentApi } from "../services/api";

function Students() {
  const { user, isAdmin } = useAuth();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchStudents() {
      try {
        if (isAdmin) {
          const res = await studentApi.getStudents();
          const list = Array.isArray(res) ? res : res.data || [];
          setStudents(list);
        } else {
          // For non-admin, load current user's student profile
          try {
            const profile = await studentApi.getStudent(user.id);
            if (profile) setStudents([profile]);
          } catch {
            // Profile may be user.id or created on demand
            setStudents([
              {
                id: user.id,
                name: user.full_name || "Student User",
                email: user.email,
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
  }, [isAdmin, user]);

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
