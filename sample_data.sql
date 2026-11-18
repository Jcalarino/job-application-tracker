-- ============================================================
-- Job Application Tracker - sample_data.sql
-- Run AFTER schema.sql. Safe to re-run: it clears the four
-- tables first, then reloads the data.
-- ============================================================

USE job_tracker_app;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE applications;
TRUNCATE TABLE contacts;
TRUNCATE TABLE jobs;
TRUNCATE TABLE companies;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- companies (IDs 1-6)
-- ------------------------------------------------------------
INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('Tech Solutions Inc',   'Technology',      'www.techsolutions.com',      'Miami',         'Florida',       'Referred by a classmate'),
('Data Analytics Corp',  'Data Science',    'www.dataanalytics.com',      'Austin',        'Texas',         NULL),
('Cloud Systems LLC',    'Cloud Computing', 'www.cloudsystems.com',       'Seattle',       'Washington',    'Remote friendly'),
('Digital Innovations',  'Software',        'www.digitalinnovations.com', 'San Francisco', 'California',    NULL),
('Smart Tech Group',     'AI/ML',           'www.smarttech.com',          'Boston',        'Massachusetts', 'Attended their career fair'),
('Sunshine Health Tech', 'Healthcare IT',   'www.sunshinehealthtech.com', 'Orlando',       'Florida',       NULL);

-- ------------------------------------------------------------
-- jobs (IDs 1-12), each with requirements JSON for Job Match
-- ------------------------------------------------------------
INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer', 'Full-time', 70000, 90000, 'https://example.com/jobs/1', '2025-01-15',
 '{"required_skills": ["Python", "SQL", "Flask"], "preferred_skills": ["Docker", "AWS"], "education": "Bachelor in CS or related field", "experience_years": 2, "remote_option": true}'),
(1, 'Database Administrator', 'Full-time', 75000, 95000, 'https://example.com/jobs/2', '2025-01-10',
 '{"required_skills": ["SQL", "MySQL", "Linux"], "preferred_skills": ["Python", "Backup and Recovery"], "education": "Bachelor degree", "experience_years": 3, "remote_option": false}'),
(2, 'Data Analyst', 'Full-time', 65000, 85000, 'https://example.com/jobs/3', '2025-01-12',
 '{"required_skills": ["SQL", "Excel", "Tableau"], "preferred_skills": ["Python", "R"], "education": "Bachelor degree", "experience_years": 1, "remote_option": false}'),
(2, 'Data Scientist', 'Full-time', 85000, 110000, 'https://example.com/jobs/4', '2025-01-07',
 '{"required_skills": ["Python", "SQL", "Machine Learning"], "preferred_skills": ["TensorFlow", "Spark"], "education": "Master in a quantitative field", "experience_years": 3, "remote_option": true}'),
(2, 'Intern - Data', 'Internship', 30000, 40000, 'https://example.com/jobs/5', '2025-01-13',
 '{"required_skills": ["SQL", "Excel"], "preferred_skills": ["Python"], "education": "Currently enrolled in college", "experience_years": 0, "remote_option": false}'),
(3, 'Cloud Engineer', 'Full-time', 80000, 100000, 'https://example.com/jobs/6', '2025-01-08',
 '{"required_skills": ["AWS", "Linux", "Python"], "preferred_skills": ["Terraform", "Docker"], "education": "Bachelor in CS or related field", "experience_years": 2, "remote_option": true}'),
(3, 'DevOps Engineer', 'Full-time', 80000, 105000, 'https://example.com/jobs/7', '2025-01-08',
 '{"required_skills": ["Docker", "Git", "Linux"], "preferred_skills": ["Kubernetes", "Python"], "education": "Bachelor in CS or related field", "experience_years": 3, "remote_option": true}'),
(4, 'Junior Developer', 'Full-time', 55000, 70000, 'https://example.com/jobs/8', '2025-01-14',
 '{"required_skills": ["Python", "Git", "HTML"], "preferred_skills": ["Flask", "CSS"], "education": "Bachelor degree", "experience_years": 0, "remote_option": false}'),
(4, 'Senior Developer', 'Full-time', 95000, 120000, 'https://example.com/jobs/9', '2025-01-14',
 '{"required_skills": ["Python", "SQL", "Flask", "Git"], "preferred_skills": ["AWS", "Docker"], "education": "Bachelor in CS or related field", "experience_years": 5, "remote_option": true}'),
(5, 'ML Engineer', 'Full-time', 90000, 115000, 'https://example.com/jobs/10', '2025-01-11',
 '{"required_skills": ["Python", "Machine Learning", "SQL"], "preferred_skills": ["PyTorch", "AWS"], "education": "Master in CS or related field", "experience_years": 3, "remote_option": true}'),
(5, 'Technical Writer', 'Contract', 55000, 75000, 'https://example.com/jobs/11', '2025-01-12',
 '{"required_skills": ["Technical Writing", "Git"], "preferred_skills": ["Markdown", "SQL"], "education": "Bachelor degree", "experience_years": 2, "remote_option": true}'),
(6, 'Junior Data Engineer', 'Full-time', 68000, 88000, 'https://example.com/jobs/12', '2025-01-16',
 '{"required_skills": ["Python", "SQL", "ETL"], "preferred_skills": ["Airflow", "AWS"], "education": "Bachelor in CS or related field", "experience_years": 1, "remote_option": false}');

-- ------------------------------------------------------------
-- applications (IDs 1-7)
-- ------------------------------------------------------------
INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1,  '2025-01-16', 'Applied',   'v2.1', TRUE,  NULL),
(3,  '2025-01-13', 'Interview', 'v2.1', TRUE,
 '{"interview_rounds": 2, "interviewers": ["Michael Chen", "Priya Patel"], "technical_questions": ["SQL joins", "Python basics", "API design"], "feedback": "Strong technical skills, good communication", "next_steps": "Final round scheduled"}'),
(6,  '2025-01-09', 'Rejected',  'v2.0', FALSE, NULL),
(8,  '2025-01-15', 'Screening', 'v2.1', TRUE,
 '{"interview_rounds": 1, "interviewers": ["David Brown"], "technical_questions": ["Git workflow"], "feedback": "Phone screen went well", "rating": 4}'),
(10, '2025-01-12', 'Offer',     'v2.1', TRUE,
 '{"interview_rounds": 3, "interviewers": ["Lisa Garcia", "Tom Reed"], "technical_questions": ["Model evaluation", "SQL window functions"], "feedback": "Excellent fit", "offer_amount": 105000}'),
(12, '2025-01-17', 'Applied',   'v3.0', TRUE,  NULL),
(9,  '2025-01-18', 'Withdrawn', 'v3.0', FALSE, NULL);

-- ------------------------------------------------------------
-- contacts (IDs 1-7)
-- ------------------------------------------------------------
INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Sarah Johnson',  'HR Manager',          'sjohnson@techsolutions.com',  '305-555-0101', 'https://linkedin.com/in/sarahjohnson', 'Met at the career fair'),
(2, 'Michael Chen',   'Technical Recruiter', 'mchen@dataanalytics.com',     '512-555-0102', NULL, NULL),
(3, 'Emily Williams', 'Hiring Manager',      'ewilliams@cloudsystems.com',  NULL,           NULL, NULL),
(4, 'David Brown',    'Senior Developer',    NULL,                          NULL,           'https://linkedin.com/in/davidbrown', 'Connect on LinkedIn for his email'),
(5, 'Lisa Garcia',    'Talent Acquisition',  'lgarcia@smarttech.com',       '617-555-0105', NULL, 'Sent thank-you note'),
(5, 'Tom Reed',       'Engineering Manager', 'treed@smarttech.com',         NULL,           NULL, NULL),
(6, 'Ana Rodriguez',  'Recruiter',           'arodriguez@sunshinehealthtech.com', '407-555-0107', NULL, NULL);

-- ------------------------------------------------------------
-- Quick check: expect 6, 12, 7, 7
-- ------------------------------------------------------------
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL SELECT 'jobs', COUNT(*) FROM jobs
UNION ALL SELECT 'applications', COUNT(*) FROM applications
UNION ALL SELECT 'contacts', COUNT(*) FROM contacts;
