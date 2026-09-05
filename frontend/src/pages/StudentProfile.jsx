import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { studentApi, skillApi } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { IconCheck, IconSparkle } from "../components/Icons";

// Curated domain knowledge relationship graph for software engineering skills
const SKILL_RELATIONSHIPS = {
  python: [
    { name: "FastAPI", category: "Backend", defaultProficiency: 3, reason: "High-performance modern Python API framework" },
    { name: "Django", category: "Backend", defaultProficiency: 3, reason: "Full-featured enterprise Python web framework" },
    { name: "Flask", category: "Backend", defaultProficiency: 3, reason: "Lightweight Python microframework" },
    { name: "SQLAlchemy", category: "Backend", defaultProficiency: 3, reason: "Python ORM & database toolkit" },
    { name: "Pandas", category: "Data Science", defaultProficiency: 3, reason: "Data manipulation & analytics" },
    { name: "NumPy", category: "Data Science", defaultProficiency: 3, reason: "Numerical & scientific computing" },
    { name: "PyTest", category: "Testing", defaultProficiency: 3, reason: "Modern Python automated testing framework" },
  ],
  fastapi: [
    { name: "Python", category: "Backend", defaultProficiency: 4, reason: "Core foundational programming language" },
    { name: "SQLAlchemy", category: "Backend", defaultProficiency: 3, reason: "Database persistence & async queries" },
    { name: "Docker", category: "DevOps", defaultProficiency: 3, reason: "Containerization for cloud deployments" },
    { name: "PostgreSQL", category: "Database", defaultProficiency: 3, reason: "Robust relational production database" },
  ],
  django: [
    { name: "Python", category: "Backend", defaultProficiency: 4, reason: "Core language" },
    { name: "PostgreSQL", category: "Database", defaultProficiency: 3, reason: "Standard production DB for Django" },
    { name: "Redis", category: "Database", defaultProficiency: 3, reason: "Caching & Celery background queues" },
  ],
  flask: [
    { name: "Python", category: "Backend", defaultProficiency: 4, reason: "Core language" },
    { name: "SQLAlchemy", category: "Backend", defaultProficiency: 3, reason: "ORM database integration" },
  ],
  javascript: [
    { name: "React", category: "Frontend", defaultProficiency: 4, reason: "Component-based interactive UI library" },
    { name: "TypeScript", category: "Frontend", defaultProficiency: 3, reason: "Typed JavaScript for large-scale codebases" },
    { name: "Node.js", category: "Backend", defaultProficiency: 3, reason: "Server-side JavaScript runtime engine" },
    { name: "Next.js", category: "Frontend", defaultProficiency: 3, reason: "Full-stack SSR React production framework" },
    { name: "HTML/CSS", category: "Frontend", defaultProficiency: 4, reason: "Fundamental web layouts and design systems" },
  ],
  react: [
    { name: "TypeScript", category: "Frontend", defaultProficiency: 3, reason: "Component prop typing and compile-time safety" },
    { name: "Next.js", category: "Frontend", defaultProficiency: 3, reason: "Server-side rendering & full-stack routes" },
    { name: "JavaScript", category: "Frontend", defaultProficiency: 4, reason: "Core underlying scripting language" },
    { name: "TailwindCSS", category: "Frontend", defaultProficiency: 4, reason: "Modern utility-first styling system" },
  ],
  mysql: [
    { name: "PostgreSQL", category: "Database", defaultProficiency: 3, reason: "Object-relational SQL database" },
    { name: "SQLAlchemy", category: "Backend", defaultProficiency: 3, reason: "Python SQL toolkit & ORM layer" },
    { name: "Redis", category: "Database", defaultProficiency: 3, reason: "Fast in-memory key-value cache" },
  ],
  docker: [
    { name: "Kubernetes", category: "DevOps", defaultProficiency: 2, reason: "Multi-node container orchestration" },
    { name: "AWS", category: "Cloud", defaultProficiency: 3, reason: "Cloud infrastructure and ECS/EKS hosting" },
    { name: "Git", category: "DevOps", defaultProficiency: 4, reason: "Version control & CI/CD automation" },
  ],
  java: [
    { name: "Spring Boot", category: "Backend", defaultProficiency: 3, reason: "Enterprise microservice application framework" },
    { name: "Hibernate", category: "Backend", defaultProficiency: 3, reason: "Java ORM & JPA persistence standard" },
    { name: "MySQL", category: "Database", defaultProficiency: 3, reason: "Relational persistence storage" },
  ],
};

function StudentProfile() {
  const { id } = useParams();
  const { user, isEmployer } = useAuth();

  const [profile, setProfile] = useState(null);
  const [skills, setSkills] = useState([]);
  const [catalogSkills, setCatalogSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Primary Add Skill Form state
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [customSkillName, setCustomSkillName] = useState("");
  const [isCustomMode, setIsCustomMode] = useState(false);
  const [proficiency, setProficiency] = useState(3);
  const [submitting, setSubmitting] = useState(false);
  const [bundleLoading, setBundleLoading] = useState(false);

  // Headline edit
  const [headline, setHeadline] = useState("");
  const [editingHeadline, setEditingHeadline] = useState(false);
  const [savingHeadline, setSavingHeadline] = useState(false);

  async function loadProfileData() {
    try {
      const [profRes, skillsRes, catalogRes] = await Promise.allSettled([
        studentApi.getStudent(id),
        studentApi.getSkills(id),
        skillApi.getSkills(),
      ]);

      if (profRes.status === "fulfilled" && profRes.value) {
        const p = profRes.value;
        setProfile(p);
        setHeadline(p.headline || "");
      }
      if (skillsRes.status === "fulfilled" && skillsRes.value) {
        const list = Array.isArray(skillsRes.value) ? skillsRes.value : skillsRes.value.data || [];
        setSkills(list);
      }
      if (catalogRes.status === "fulfilled" && catalogRes.value) {
        const cList = Array.isArray(catalogRes.value) ? catalogRes.value : catalogRes.value.data || [];
        setCatalogSkills(cList);
        if (cList.length > 0 && !selectedSkillId) {
          setSelectedSkillId(String(cList[0].id));
        }
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

  // Determine current active skill name for related suggestions
  const getActiveSkillName = () => {
    if (isCustomMode && customSkillName.trim()) {
      return customSkillName.trim();
    }
    const catSkill = catalogSkills.find((s) => String(s.id) === String(selectedSkillId));
    return catSkill ? catSkill.name : "";
  };

  const activeSkillName = getActiveSkillName();

  // Find related skills for the currently selected/input skill
  const getRelatedSkillsForActive = () => {
    if (!activeSkillName) return [];
    const key = activeSkillName.toLowerCase().trim();
    return SKILL_RELATIONSHIPS[key] || [];
  };

  const relatedSkills = getRelatedSkillsForActive();

  // Find existing profile skill by name
  const findAcquiredSkill = (skillName) => {
    if (!skillName || !skills) return null;
    return skills.find(
      (s) => (s.skill_name || "").toLowerCase().trim() === skillName.toLowerCase().trim()
    );
  };

  const handleAddSkill = async (e) => {
    if (e) e.preventDefault();

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      if (isCustomMode) {
        if (!customSkillName.trim()) {
          setError("Please enter a skill or library name.");
          setSubmitting(false);
          return;
        }
        await studentApi.addSkill(id, {
          skill_name: customSkillName.trim(),
          proficiency: Number(proficiency),
        });
        setSuccess(`Skill "${customSkillName.trim()}" added with Level ${proficiency}/5!`);
        setCustomSkillName("");
        setIsCustomMode(false);
      } else {
        if (!selectedSkillId) return;
        await studentApi.addSkill(id, {
          skill_id: Number(selectedSkillId),
          proficiency: Number(proficiency),
        });
        const skillObj = catalogSkills.find((s) => String(s.id) === String(selectedSkillId));
        setSuccess(`Skill "${skillObj ? skillObj.name : "Skill"}" saved with Level ${proficiency}/5!`);
      }
      await loadProfileData();
    } catch (err) {
      setError(err.message || "Could not add skill");
    } finally {
      setSubmitting(false);
    }
  };

  // 1-Click addition of an individual related skill
  const handleAddIndividualRelatedSkill = async (relSkill, customLevel) => {
    setError("");
    setSuccess("");
    try {
      await studentApi.addSkill(id, {
        skill_name: relSkill.name,
        category: relSkill.category,
        proficiency: customLevel || relSkill.defaultProficiency || 3,
      });
      setSuccess(`✓ Added complementary library "${relSkill.name}" (Level ${customLevel || relSkill.defaultProficiency || 3}/5)!`);
      await loadProfileData();
    } catch (err) {
      setError(err.message || `Failed to add ${relSkill.name}`);
    }
  };

  // Bundle Add all missing related skills in one click
  const handleBundleAddRelated = async () => {
    if (!relatedSkills || relatedSkills.length === 0) return;
    setBundleLoading(true);
    setError("");
    setSuccess("");

    const unadded = relatedSkills.filter((rel) => !findAcquiredSkill(rel.name));
    if (unadded.length === 0) {
      setSuccess("All related libraries are already in your profile!");
      setBundleLoading(false);
      return;
    }

    try {
      for (const rel of unadded) {
        await studentApi.addSkill(id, {
          skill_name: rel.name,
          category: rel.category,
          proficiency: rel.defaultProficiency || 3,
        });
      }
      setSuccess(`⚡ Successfully bundled and added ${unadded.length} related ${activeSkillName} libraries to your profile!`);
      await loadProfileData();
    } catch (err) {
      setError(err.message || "Error adding skill bundle");
    } finally {
      setBundleLoading(false);
    }
  };

  const handleDeleteSkill = async (skillId) => {
    try {
      await studentApi.deleteSkill(id, skillId);
      setSuccess("Skill removed from profile.");
      await loadProfileData();
    } catch (err) {
      setError(err.message || "Failed to remove skill");
    }
  };

  const handleSaveHeadline = async () => {
    setSavingHeadline(true);
    setError("");
    try {
      await studentApi.updateStudent(id, { headline: headline.trim() });
      setSuccess("Professional headline updated!");
      setEditingHeadline(false);
      await loadProfileData();
    } catch (err) {
      setError(err.message || "Failed to update headline");
    } finally {
      setSavingHeadline(false);
    }
  };

  // Render visual proficiency meter
  const renderProficiencyMeter = (level) => {
    const filled = Math.min(5, Math.max(0, level || 0));
    return "●".repeat(filled) + "○".repeat(5 - filled);
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
          <p>Verified technical competencies, frameworks, and library proficiency</p>
        </div>

        {isEmployer && (
          <Link to="/dashboard" className="btn-secondary">
            ← Back to Candidate Discovery
          </Link>
        )}
      </div>

      {error && <div className="alert-error-banner">{error}</div>}
      {success && <div className="alert-success-banner">{success}</div>}

      {profile && (
        <div className="profile-hero-card">
          <div className="profile-hero-avatar">
            {(profile.name || profile.full_name || "S")[0].toUpperCase()}
          </div>
          <div className="profile-hero-details" style={{ flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "10px" }}>
              <div>
                <h2>{profile.name || profile.full_name}</h2>
                <p className="profile-hero-email">✉ {profile.email}</p>
              </div>

              {!isEmployer && !editingHeadline && (
                <button
                  className="btn-outline-sm"
                  onClick={() => setEditingHeadline(true)}
                  style={{ fontSize: "0.75rem", padding: "4px 10px" }}
                >
                  ✎ Edit Headline
                </button>
              )}
            </div>

            {editingHeadline ? (
              <div style={{ marginTop: "10px", display: "flex", gap: "8px", alignItems: "center" }}>
                <input
                  type="text"
                  value={headline}
                  onChange={(e) => setHeadline(e.target.value)}
                  placeholder="e.g. Full Stack Python & React Engineer"
                  className="custom-input"
                  style={{ maxWidth: "360px", padding: "6px 12px" }}
                />
                <button
                  className="btn-primary-sm"
                  onClick={handleSaveHeadline}
                  disabled={savingHeadline}
                >
                  {savingHeadline ? "Saving..." : "Save"}
                </button>
                <button
                  className="btn-outline-sm"
                  onClick={() => setEditingHeadline(false)}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <p className="profile-hero-headline">
                "{profile.headline || "Seeking Software Engineering Opportunities"}"
              </p>
            )}
          </div>
        </div>
      )}

      {/* Add Skill Widget */}
      {!isEmployer && (
        <div className="dashboard-section" style={{ marginTop: "1.5rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap", gap: "10px" }}>
            <div>
              <h3 style={{ margin: 0 }}>Add Verified Competency</h3>
              <p style={{ margin: "4px 0 0 0", fontSize: "0.825rem", color: "var(--ink-muted)" }}>
                Add core languages, frameworks, or specialized libraries to match employer requisitions.
              </p>
            </div>

            <button
              type="button"
              className="btn-outline-sm"
              onClick={() => setIsCustomMode(!isCustomMode)}
              style={{ fontSize: "0.8rem" }}
            >
              {isCustomMode ? "← Select from Catalog" : "+ Type Custom Library / Skill"}
            </button>
          </div>

          <form className="inline-add-skill-form" onSubmit={handleAddSkill}>
            {isCustomMode ? (
              <div className="form-group" style={{ flex: 2 }}>
                <label>Custom Skill or Library Name:</label>
                <input
                  type="text"
                  value={customSkillName}
                  onChange={(e) => setCustomSkillName(e.target.value)}
                  placeholder="e.g. FastAPI, Django, Flask, Pandas..."
                  className="custom-input"
                  required
                />
              </div>
            ) : (
              <div className="form-group" style={{ flex: 2 }}>
                <label>Select Skill from Catalog:</label>
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
            )}

            <div className="form-group" style={{ flex: 1.2 }}>
              <label>Proficiency (1 to 5):</label>
              <select
                value={proficiency}
                onChange={(e) => setProficiency(e.target.value)}
                className="custom-select"
              >
                <option value="1">Level 1 - Novice (Familiar with syntax)</option>
                <option value="2">Level 2 - Beginner (Can build toy apps)</option>
                <option value="3">Level 3 - Intermediate (Production ready)</option>
                <option value="4">Level 4 - Advanced (Architectural depth)</option>
                <option value="5">Level 5 - Expert (Mastery & performance)</option>
              </select>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={submitting}
              style={{ alignSelf: "flex-end" }}
            >
              {submitting ? "Saving..." : "+ Save Skill"}
            </button>
          </form>

          {/* Related Skills & Libraries Ecosystem Section */}
          {relatedSkills && relatedSkills.length > 0 && (
            <div className="related-skills-ecosystem-box" style={{ marginTop: "1.5rem" }}>
              <div className="related-ecosystem-header">
                <div>
                  <div className="ecosystem-title-row">
                    <IconSparkle size={18} />
                    <h4>Related Skills & Libraries for {activeSkillName}</h4>
                  </div>
                  <p className="ecosystem-subtitle">
                    Employers searching for <strong>{activeSkillName}</strong> expect proficiency in companion frameworks and tooling.
                  </p>
                </div>

                <button
                  type="button"
                  className="btn-secondary btn-sm bundle-add-btn"
                  onClick={handleBundleAddRelated}
                  disabled={bundleLoading}
                >
                  {bundleLoading ? "Bundling..." : `⚡ Add Entire ${activeSkillName} Stack`}
                </button>
              </div>

              <div className="related-skills-grid">
                {relatedSkills.map((rel) => {
                  const existing = findAcquiredSkill(rel.name);
                  return (
                    <div
                      key={rel.name}
                      className={`related-skill-item-card ${existing ? "is-acquired" : ""}`}
                    >
                      <div className="related-skill-item-header">
                        <div>
                          <strong className="related-skill-name">{rel.name}</strong>
                          <span className="badge-category" style={{ marginLeft: "8px", fontSize: "0.7rem" }}>
                            {rel.category}
                          </span>
                        </div>
                        {existing && (
                          <span className="acquired-badge-pill">
                            <IconCheck size={13} /> Level {existing.proficiency}/5
                          </span>
                        )}
                      </div>

                      <p className="related-skill-reason">{rel.reason}</p>

                      <div className="related-skill-action-row">
                        {existing ? (
                          <span style={{ fontSize: "0.775rem", color: "var(--accent-forest)", fontWeight: 600 }}>
                            Verified in profile ({renderProficiencyMeter(existing.proficiency)})
                          </span>
                        ) : (
                          <div style={{ display: "flex", gap: "6px", alignItems: "center", width: "100%" }}>
                            <button
                              type="button"
                              className="btn-outline-sm"
                              onClick={() => handleAddIndividualRelatedSkill(rel, rel.defaultProficiency)}
                              style={{ flex: 1, justifyContent: "center", display: "inline-flex", alignItems: "center", gap: "4px" }}
                            >
                              + Add {rel.name} ({rel.defaultProficiency}/5)
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Verified Skills Table */}
      <div className="dashboard-section" style={{ marginTop: "1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h3 style={{ margin: 0 }}>Verified Acquired Skills & Libraries ({skills.length})</h3>
          <span style={{ fontSize: "0.85rem", color: "var(--ink-muted)" }}>
            Used for real-time weighted role matching & employer skill searches
          </span>
        </div>

        {skills.length === 0 ? (
          <div className="empty-talent-card">
            <p>No skills added to this profile yet. Use the form above to add your technical skills and frameworks.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Skill / Library</th>
                  <th>Category</th>
                  <th>Proficiency Level</th>
                  <th>Competency Meter</th>
                  {!isEmployer && <th>Action</th>}
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
                    <td style={{ fontFamily: "var(--font-mono)", letterSpacing: "2px", color: "var(--brand-primary)" }}>
                      {renderProficiencyMeter(s.proficiency)}
                    </td>
                    {!isEmployer && (
                      <td>
                        <button
                          className="btn-danger-sm"
                          onClick={() => handleDeleteSkill(s.skill_id)}
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

export default StudentProfile;
