-- ============================================================
-- Job Application Tracker - schema.sql
-- COP4751 Course Project
--
-- Recreates the full database from scratch.
-- Safe to re-run: it drops and rebuilds only the four project
-- tables inside job_tracker_app. Re-running erases their data.
-- ============================================================

CREATE DATABASE IF NOT EXISTS job_tracker_app
    DEFAULT CHARACTER SET utf8mb4;

USE job_tracker_app;

-- Drop in reverse dependency order (children before parents)
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS contacts;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS companies;

-- ------------------------------------------------------------
-- companies
-- ------------------------------------------------------------
CREATE TABLE companies (
    company_id   INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    industry     VARCHAR(50),
    website      VARCHAR(200),
    city         VARCHAR(50),
    state        VARCHAR(50),
    notes        TEXT
);

-- ------------------------------------------------------------
-- jobs
-- requirements is JSON, e.g.
--   {"required_skills": ["Python","SQL"], "preferred_skills": [...],
--    "experience_years": 2, "remote_option": true}
-- ------------------------------------------------------------
CREATE TABLE jobs (
    job_id       INT AUTO_INCREMENT PRIMARY KEY,
    company_id   INT NOT NULL,
    job_title    VARCHAR(100) NOT NULL,
    job_type     ENUM('Full-time','Part-time','Contract','Internship'),
    salary_min   INT,
    salary_max   INT,
    job_url      VARCHAR(300),
    date_posted  DATE,
    requirements JSON,
    CONSTRAINT fk_jobs_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- applications
-- interview_data is JSON, e.g.
--   {"interview_rounds": 2, "interviewers": ["A","B"], "feedback": "..."}
-- ------------------------------------------------------------
CREATE TABLE applications (
    application_id    INT AUTO_INCREMENT PRIMARY KEY,
    job_id            INT NOT NULL,
    application_date  DATE NOT NULL,
    status            ENUM('Applied','Screening','Interview','Offer','Rejected','Withdrawn')
                      NOT NULL DEFAULT 'Applied',
    resume_version    VARCHAR(50),
    cover_letter_sent BOOLEAN DEFAULT FALSE,
    interview_data    JSON,
    CONSTRAINT fk_applications_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- contacts
-- ------------------------------------------------------------
CREATE TABLE contacts (
    contact_id   INT AUTO_INCREMENT PRIMARY KEY,
    company_id   INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title        VARCHAR(100),
    email        VARCHAR(100),
    phone        VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes        TEXT,
    CONSTRAINT fk_contacts_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Indexes (from Assignment 3)
-- idx_company_type also serves lookups by company_id alone,
-- so jobs.company_id does not need its own index.
-- ------------------------------------------------------------
CREATE INDEX idx_job_title        ON jobs(job_title);
CREATE INDEX idx_company_type     ON jobs(company_id, job_type);
CREATE INDEX idx_app_status       ON applications(status);
CREATE INDEX idx_company_industry ON companies(industry);

-- ------------------------------------------------------------
-- Quick check: should list applications, companies, contacts, jobs
-- ------------------------------------------------------------
SHOW TABLES;
