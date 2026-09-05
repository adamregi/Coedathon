PHASE 9: ANALYSIS RUNS
-- =========================================================

CREATE TABLE analysis_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,

    student_id INT NOT NULL,

    job_id INT NOT NULL,

    calculated_match DECIMAL(5,2) NOT NULL,

    algorithm_version VARCHAR(50) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_analysis_runs_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_analysis_runs_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(job_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT check_calculated_match
        CHECK (calculated_match BETWEEN 0 AND 100)
);


-- =========================================================
-- PHASE 9: ANALYSIS ITEMS
-- =========================================================

CREATE TABLE analysis_items (
    id INT AUTO_INCREMENT PRIMARY KEY,

    analysis_run_id INT NOT NULL,

    skill_id INT NOT NULL,

    current_level INT NOT NULL DEFAULT 0,

    required_level INT NOT NULL,

    gap INT NOT NULL,

    status VARCHAR(50) NOT NULL,

    CONSTRAINT fk_analysis_items_run
        FOREIGN KEY (analysis_run_id)
        REFERENCES analysis_runs(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_analysis_items_skill
        FOREIGN KEY (skill_id)
        REFERENCES skills(skill_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT check_current_level
        CHECK (current_level BETWEEN 0 AND 5),

    CONSTRAINT check_analysis_required_level
        CHECK (required_level BETWEEN 1 AND 5)
);


-- =========================================================
-- PHASE 10: RECOMMENDATIONS
-- =========================================================

CREATE TABLE recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,

    student_id INT NOT NULL,

    job_id INT NOT NULL,

    skill_id INT NOT NULL,

    current_level INT NOT NULL DEFAULT 0,

    target_level INT NOT NULL,

    priority VARCHAR(50) NOT NULL,

    reason TEXT NOT NULL,

    analysis_run_id INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_recommendations_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_recommendations_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(job_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_recommendations_skill
        FOREIGN KEY (skill_id)
        REFERENCES skills(skill_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_recommendations_analysis
        FOREIGN KEY (analysis_run_id)
        REFERENCES analysis_runs(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT check_recommendation_current_level
        CHECK (current_level BETWEEN 0 AND 5),

    CONSTRAINT check_recommendation_target_level
        CHECK (target_level BETWEEN 1 AND 5)
);


-- =========================================================
-- PHASE 11: DATABASE OPTIMIZATION
-- =========================================================


-- Student Skills indexes

CREATE INDEX idx_student_skills_student
ON student_skills(student_id);

CREATE INDEX idx_student_skills_skill
ON student_skills(skill_id);

CREATE INDEX idx_student_skills_student_skill
ON student_skills(student_id, skill_id);


-- Job Skills indexes

CREATE INDEX idx_job_skills_job
ON job_skills(job_id);

CREATE INDEX idx_job_skills_skill
ON job_skills(skill_id);

CREATE INDEX idx_job_skills_job_skill
ON job_skills(job_id, skill_id);


-- Applications indexes

CREATE INDEX idx_applications_student
ON applications(student_id);

CREATE INDEX idx_applications_job
ON applications(job_id);

CREATE INDEX idx_applications_student_job
ON applications(student_id, job_id);


-- Recommendations indexes

CREATE INDEX idx_recommendations_student
ON recommendations(student_id);

CREATE INDEX idx_recommendations_job
ON recommendations(job_id);

CREATE INDEX idx_recommendations_student_job
ON recommendations(student_id, job_id);


-- Analysis indexes

CREATE INDEX idx_analysis_runs_student
ON analysis_runs(student_id);

CREATE INDEX idx_analysis_runs_job
ON analysis_runs(job_id);

CREATE INDEX idx_analysis_items_run
ON analysis_items(analysis_run_id);

CREATE INDEX idx_analysis_items_skill
ON analysis_items(skill_id);

