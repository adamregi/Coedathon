import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { jobApi } from "../services/api";
import ErrorMessage from "../components/ErrorMessage";

function JobForm() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    title: "",
    company_name: "",
    description: "",
    department: "",
    location: "",
    salary_range: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title || !form.company_name) {
      setError("Job Title and Company Name are required.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const created = await jobApi.createJob({
        ...form,
        requirements: [],
      });
      navigate(`/jobs/${created.id}`);
    } catch (err) {
      setError(err.message || "Failed to post job");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Post a New Job Opening</h1>
          <p className="page-subtitle">Define role requirements and open position parameters to match against talent skill sets.</p>
        </div>
        <Link to="/jobs" className="btn btn-secondary">
          ← Cancel
        </Link>
      </div>

      {error && <ErrorMessage message={error} />}

      <div className="card shadow-sm" style={{ maxWidth: "720px" }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Job Title *</label>
            <input
              name="title"
              className="form-control"
              value={form.title}
              onChange={handleChange}
              placeholder="e.g. Senior Backend Engineer"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Company Name *</label>
            <input
              name="company_name"
              className="form-control"
              value={form.company_name}
              onChange={handleChange}
              placeholder="e.g. Acme Corporation"
              required
            />
          </div>

          <div className="grid-2-col">
            <div className="form-group">
              <label className="form-label">Department</label>
              <input
                name="department"
                className="form-control"
                value={form.department}
                onChange={handleChange}
                placeholder="e.g. Platform Engineering"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Location</label>
              <input
                name="location"
                className="form-control"
                value={form.location}
                onChange={handleChange}
                placeholder="e.g. Remote / Bangalore"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Salary Range</label>
            <input
              name="salary_range"
              className="form-control"
              value={form.salary_range}
              onChange={handleChange}
              placeholder="e.g. $120,000 - $150,000"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Role Description</label>
            <textarea
              name="description"
              className="form-control"
              rows={4}
              value={form.description}
              onChange={handleChange}
              placeholder="Provide role responsibilities, mission, and required qualifications..."
            />
          </div>

          <div className="mt-4 flex justify-end">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Publishing Job..." : "Publish Job Opening →"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default JobForm;
