 PHASE 8: APPLICATIONS
-- =========================================================

CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,

    student_id INT NOT NULL,

    job_id INT NOT NULL,

    match_percent DECIMAL(5,2),

    status VARCHAR(50) NOT NULL DEFAULT 'applied',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_applications_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_applications_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(job_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT unique_student_job_application
        UNIQUE (student_id, job_id),

    CONSTRAINT check_match_percent
        CHECK (match_percent IS NULL OR
               match_percent BETWEEN 0 AND 100)
);


