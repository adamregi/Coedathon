import axios from "axios";

// Primary Axios instance connecting to FastAPI backend
const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: Attach JWT bearer access token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Unwrap standard envelope { data, meta, error } or handle 401
api.interceptors.response.use(
  (response) => {
    // If backend uses standard envelope { data, meta, error }, unwrap or provide fallback
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Clear token on authentication failure
      localStorage.removeItem("user");
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      if (window.location.pathname !== "/login" && window.location.pathname !== "/signup") {
        window.location.href = "/login";
      }
    }
    const message =
      error.response?.data?.error?.message ||
      error.response?.data?.message ||
      error.message ||
      "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);

// ---------------------------------------------------------------------------
// 1. Authentication APIs
// ---------------------------------------------------------------------------
export const authApi = {
  login: async (email, password) => {
    const res = await api.post("/api/auth/login", { email, password });
    return res.data?.data || res.data;
  },
  register: async ({ email, password, full_name, role }) => {
    const res = await api.post("/api/auth/register", {
      email,
      password,
      full_name,
      role: role || "student",
    });
    return res.data?.data || res.data;
  },
  getMe: async () => {
    const res = await api.get("/api/auth/me");
    return res.data?.data || res.data;
  },
};

// ---------------------------------------------------------------------------
// 2. Dashboard APIs
// ---------------------------------------------------------------------------
export const dashboardApi = {
  getMetrics: async () => {
    const res = await api.get("/api/dashboard");
    return res.data?.data || res.data;
  },
};

// ---------------------------------------------------------------------------
// 3. Students APIs
// ---------------------------------------------------------------------------
export const studentApi = {
  getStudents: async () => {
    const res = await api.get("/api/students");
    return res.data?.data || res.data;
  },
  getStudent: async (id) => {
    const res = await api.get(`/api/students/${id}`);
    return res.data?.data || res.data;
  },
  createStudent: async (data) => {
    const res = await api.post("/api/students", data);
    return res.data?.data || res.data;
  },
  updateStudent: async (id, data) => {
    const res = await api.put(`/api/students/${id}`, data);
    return res.data?.data || res.data;
  },
  getSkills: async (id) => {
    const res = await api.get(`/api/students/${id}/skills`);
    return res.data?.data || res.data;
  },
  addSkill: async (studentId, { skill_id, proficiency }) => {
    const res = await api.post(`/api/students/${studentId}/skills`, {
      skill_id: Number(skill_id),
      proficiency: Number(proficiency),
    });
    return res.data?.data || res.data;
  },
  deleteSkill: async (studentId, skillId) => {
    const res = await api.delete(`/api/students/${studentId}/skills/${skillId}`);
    return res.data?.data || res.data;
  },
};

// ---------------------------------------------------------------------------
// 4. Skills Catalog APIs
// ---------------------------------------------------------------------------
export const skillApi = {
  getSkills: async () => {
    const res = await api.get("/api/skills");
    return res.data?.data || res.data;
  },
  createSkill: async (data) => {
    const res = await api.post("/api/skills", data);
    return res.data?.data || res.data;
  },
  getSkill: async (id) => {
    const res = await api.get(`/api/skills/${id}`);
    return res.data?.data || res.data;
  },
  updateSkill: async (id, data) => {
    const res = await api.put(`/api/skills/${id}`, data);
    return res.data?.data || res.data;
  },
  deleteSkill: async (id) => {
    const res = await api.delete(`/api/skills/${id}`);
    return res.data?.data || res.data;
  },
};

// ---------------------------------------------------------------------------
// 5. Jobs APIs
// ---------------------------------------------------------------------------
export const jobApi = {
  getJobs: async () => {
    const res = await api.get("/api/jobs");
    return res.data?.data || res.data;
  },
  getJob: async (id) => {
    const res = await api.get(`/api/jobs/${id}`);
    return res.data?.data || res.data;
  },
  createJob: async (data) => {
    const res = await api.post("/api/jobs", data);
    return res.data?.data || res.data;
  },
  updateJob: async (id, data) => {
    const res = await api.put(`/api/jobs/${id}`, data);
    return res.data?.data || res.data;
  },
  deleteJob: async (id) => {
    const res = await api.delete(`/api/jobs/${id}`);
    return res.data?.data || res.data;
  },
  getRequirements: async (jobId) => {
    const res = await api.get(`/api/jobs/${jobId}/skills`);
    return res.data?.data || res.data;
  },
  addRequirement: async (jobId, { skill_id, required_level, required_proficiency, mandatory }) => {
    const res = await api.post(`/api/jobs/${jobId}/skills`, {
      skill_id: Number(skill_id),
      required_proficiency: Number(required_proficiency ?? required_level ?? 1),
      mandatory: Boolean(mandatory),
    });
    return res.data?.data || res.data;
  },
  deleteRequirement: async (jobId, skillId) => {
    const res = await api.delete(`/api/jobs/${jobId}/skills/${skillId}`);
    return res.data?.data || res.data;
  },
};

// ---------------------------------------------------------------------------
// 6. Skill Gap Analysis & Right Candidate Discovery APIs
// ---------------------------------------------------------------------------
export const analysisApi = {
  triggerSkillGap: async (studentId, jobId) => {
    const res = await api.post(`/api/students/${studentId}/jobs/${jobId}/skill-gap`);
    return res.data?.data || res.data;
  },
  getRecommendations: async (studentId, jobId) => {
    const res = await api.get(`/api/students/${studentId}/jobs/${jobId}/recommendations`);
    return res.data?.data || res.data;
  },
  // Candidate discovery for employers
  getCandidateRankings: async (jobId, { skill, min_proficiency } = {}) => {
    const params = {};
    if (skill) params.skill = skill;
    if (min_proficiency) params.min_proficiency = min_proficiency;
    const res = await api.get(`/api/v1/analysis/jobs/${jobId}/candidates`, { params });
    return res.data?.data || res.data;
  },
  getCandidateProfile: async (jobId, studentId) => {
    const res = await api.get(`/api/v1/analysis/jobs/${jobId}/candidates/${studentId}/profile`);
    return res.data?.data || res.data;
  },
};

// ---------------------------------------------------------------------------
// 7. Applications APIs
// ---------------------------------------------------------------------------
export const applicationApi = {
  getApplications: async () => {
    const res = await api.get("/api/applications");
    return res.data?.data || res.data;
  },
  getApplication: async (id) => {
    const res = await api.get(`/api/applications/${id}`);
    return res.data?.data || res.data;
  },
  submitApplication: async (jobId) => {
    const res = await api.post("/api/applications", { job_id: Number(jobId) });
    return res.data?.data || res.data;
  },
  updateStatus: async (id, status) => {
    const res = await api.patch(`/api/applications/${id}/status`, { status });
    return res.data?.data || res.data;
  },
  withdrawApplication: async (id) => {
    const res = await api.post(`/api/applications/${id}/withdraw`);
    return res.data?.data || res.data;
  },
};

export default api;
