import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { studentApi } from "../services/api";
import { useAuth } from "../context/AuthContext";
import ErrorMessage from "../components/ErrorMessage";

function StudentForm() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [form, setForm] = useState({
    headline: "",
    education: "",
    graduation_year: new Date().getFullYear(),
    bio: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // If student user has an existing profile, prefill
    const loadProfile = async () => {
      if (user?.id) {
        try {
          const profile = await studentApi.getStudent(user.id);
          if (profile) {
            setForm({
              headline: profile.headline || "",
              education: profile.education || "",
              graduation_year: profile.graduation_year || new Date().getFullYear(),
              bio: profile.bio || "",
            });
          }
        } catch {
          // New profile, ignore
        }
      }
    };
    loadProfile();
  }, [user]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: name === "graduation_year" ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (user?.id) {
        // Try update first
        try {
          await studentApi.updateStudent(user.id, form);
          navigate(`/students/${user.id}`);
          return;
        } catch {
          // If profile doesn't exist yet, create
          const created = await studentApi.createStudent(form);
          navigate(`/students/${created.id}`);
          return;
        }
      }
      const res = await studentApi.createStudent(form);
      navigate(`/students/${res.id}`);
    } catch (err) {
      setError(err.message || "Failed to save profile.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Candidate Profile Setup</h1>
          <p className="page-subtitle">
            Configure candidate background, academic track, and career objective to optimize matching accuracy.
          </p>
        </div>
        <Link to="/students" className="btn btn-secondary">
          ← Back to Candidates
        </Link>
      </div>

      {error && <ErrorMessage message={error} />}

      <div className="card shadow-sm" style={{ maxWidth: "680px" }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Professional Headline *</label>
            <input
              type="text"
              name="headline"
              className="form-control"
              value={form.headline}
              onChange={handleChange}
              placeholder="e.g. Aspiring Full-Stack Software Engineer | React & Python"
              required
            />
          </div>

          <div className="grid-2-col">
            <div className="form-group">
              <label className="form-label">Degree / Institution *</label>
              <input
                type="text"
                name="education"
                className="form-control"
                value={form.education}
                onChange={handleChange}
                placeholder="e.g. B.Tech in Computer Science, IIT Madras"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Graduation Year</label>
              <input
                type="number"
                name="graduation_year"
                className="form-control"
                min="1990"
                max="2035"
                value={form.graduation_year}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Professional Summary / Bio</label>
            <textarea
              name="bio"
              className="form-control"
              rows={4}
              value={form.bio}
              onChange={handleChange}
              placeholder="Highlight your key technical achievements, hackathons, and career focus..."
            />
          </div>

          <div className="mt-4 flex justify-end gap-2">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? "Saving Profile..." : "Save Candidate Profile →"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default StudentForm;
