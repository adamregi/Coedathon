PHASE 3: STUDENTS
-- =========================================================

CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL UNIQUE,

    name VARCHAR(100) NOT NULL,

    email VARCHAR(150) NOT NULL UNIQUE,

    headline VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_students_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- =========================================================
-- PHASE 4: SKILLS
-- =========================================================

CREATE TABLE skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(100) NOT NULL UNIQUE,

    category VARCHAR(100) NOT NULL
);


-- =========================================================
-- PHASE 5: STUDENT SKILLS
-- =========================================================

CREATE TABLE student_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,

    student_id INT NOT NULL,

    skill_id INT NOT NULL,

    proficiency INT NOT NULL,

    CONSTRAINT fk_student_skills_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_student_skills_skill
        FOREIGN KEY (skill_id)
        REFERENCES skills(skill_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT unique_student_skill
        UNIQUE (student_id, skill_id),

    CONSTRAINT check_student_proficiency
        CHECK (proficiency BETWEEN 1 AND 5)
);


-- =========================================================
-- PHASE 6: JOBS
-- =========================================================

CREATE TABLE jobs (
    job_id INT AUTO_INCREMENT PRIMARY KEY,

    title VARCHAR(150) NOT NULL,

    company VARCHAR(150) NOT NULL,

    location VARCHAR(150) NOT NULL,

    status VARCHAR(50) NOT NULL DEFAULT 'active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- =========================================================
-- PHASE 7: JOB SKILLS
-- =========================================================

CREATE TABLE job_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,

    job_id INT NOT NULL,

    skill_id INT NOT NULL,

    required_level INT NOT NULL,

    mandatory BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_job_skills_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(job_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_job_skills_skill
        FOREIGN KEY (skill_id)
        REFERENCES skills(skill_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT unique_job_skill
        UNIQUE (job_id, skill_id),

    CONSTRAINT check_required_level
        CHECK (required_level BETWEEN 1 AND 5)
);

