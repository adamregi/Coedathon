import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { studentApi, skillApi } from "../services/api";

function StudentProfile() {
  const { id } = useParams();
  const [profile, setProfile] = useState(null);
  const [skills, setSkills] = useState([]);
  const [catalogSkills, setCatalogSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Add Skill Form state
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [proficiency, setProficiency] = useState(3);
  const [submitting, setSubmitting] = useState(false);

  async function loadProfileData() {
    try {
      const [profRes, skillsRes, catalogRes] = await Promise.allSettled([
        studentApi.getStudent(id),
        studentApi.getSkills(id),
        skillApi.getSkills(),
      ]);

      if (profRes.status === "fulfilled" && profRes.value) {
        setProfile(profRes.value);
      }
      if (skillsRes.status === "fulfilled" && skillsRes.value) {
        const list = Array.isArray(skillsRes.value) ? skillsRes.value : skillsRes.value.data || [];
        setSkills(list);
      }
      if (catalogRes.status === "fulfilled" && catalogRes.value) {
        const cList = Array.isArray(catalogRes.value) ? catalogRes.value : catalogRes.value.data || [];
        setCatalogSkills(cList);
        if (cList.length > 0) setSelectedSkillId(String(cList[0].id));
      }
    } catch (err) {
      setError("Failed to load student profile");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProfileData();
  }, [id]);

  const handleAddSkill = async (e) => {
    e.preventDefault();
    if (!selectedSkillId) return;

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      await studentApi.addSkill(id, {
        skill_id: Number(selectedSkillId),
        proficiency: Number(proficiency),
      });
      setSuccess("Skill added/updated successfully!");
      await loadProfileData();
    } catch (err) {
      setError(err.message || "Could not add skill");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteSkill = async (skillId) => {
    try {
      await studentApi.deleteSkill(id, skillId);
      setSuccess("Skill removed.");
      await loadProfileData();
    } catch (err) {
      setError(err.message || "Failed to remove skill");
    }
  };

  if (loading) {
    return (
      <div className="loading-state-card">
        <div className="spinner"></div>
        <p>Loading candidate profile from database...</p>
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1>Candidate Skill Profile</h1>
          <p>Verified competency records and proficiency levels</p>
        </div>
      </div>

      {error && <div className="alert-error-banner">{error}</div>}
      {success && <div className="alert-success-banner">{success}</div>}

      {profile && (
        <div className="profile-hero-card">
          <div className="profile-hero-avatar">
            {(profile.name || profile.full_name || "S")[0].toUpperCase()}
          </div>
          <div className="profile-hero-details">
            <h2>{profile.name || profile.full_name}</h2>
            <p className="profile-hero-email">✉ {profile.email}</p>
            <p className="profile-hero-headline">
              "{profile.headline || "Seeking Software Engineering Opportunities"}"
            </p>
          </div>
        </div>
      )}

      {/* Add Skill Widget */}
      <div className="dashboard-section" style={{ marginTop: "1.5rem" }}>
        <h3>Add or Update Acquired Skill</h3>
        <form className="inline-add-skill-form" onSubmit={handleAddSkill}>
          <div className="form-group" style={{ flex: 2 }}>
            <label>Select Skill:</label>
            <select
              value={selectedSkillId}
              onChange={(e) => setSelectedSkillId(e.target.value)}
              className="custom-select"
            >
              {catalogSkills.length === 0 && <option value="">No catalog skills found</option>}
              {catalogSkills.map((sk) => (
                <option key={sk.id} value={sk.id}>
                  {sk.name} ({sk.category || "General"})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ flex: 1 }}>
            <label>Proficiency (1 to 5):</label>
            <select
              value={proficiency}
              onChange={(e) => setProficiency(e.target.value)}
              className="custom-select"
            >
              <option value="1">Level 1 - Novice</option>
              <option value="2">Level 2 - Beginner</option>
              <option value="3">Level 3 - Intermediate</option>
              <option value="4">Level 4 - Advanced</option>
              <option value="5">Level 5 - Expert</option>
            </select>
          </div>

          <button type="submit" className="btn-primary" disabled={submitting} style={{ alignSelf: "flex-end" }}>
            {submitting ? "Saving..." : "+ Save Skill"}
          </button>
        </form>
      </div>

      {/* Skills Table */}
      <div className="dashboard-section" style={{ marginTop: "1.5rem" }}>
        <h3>Verified Acquired Skills ({skills.length})</h3>

        {skills.length === 0 ? (
          <div className="empty-talent-card">
            <p>No skills added to this profile yet. Use the form above to add skills.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Skill Name</th>
                  <th>Category</th>
                  <th>Proficiency Level</th>
                  <th>Rating</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {skills.map((s) => (
                  <tr key={s.id || s.skill_id}>
                    <td>
                      <strong>{s.skill_name || `Skill #${s.skill_id}`}</strong>
                    </td>
                    <td>
                      <span className="badge-category">{s.category || "General"}</span>
                    </td>
                    <td>
                      <span className="badge-proficiency">Level {s.proficiency} of 5</span>
                    </td>
                    <td>{"★".repeat(s.proficiency) + "☆".repeat(5 - s.proficiency)}</td>
                    <td>
                      <button
                        className="btn-danger-sm"
                        onClick={() => handleDeleteSkill(s.skill_id)}
                      >
                        ✕ Remove
                      </button>
                    </td>
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

export default StudentProfile;
