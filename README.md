# Job Application Tracker

A full-stack web app for tracking a job search. It stores companies, job postings,
applications, and contacts in MySQL, and includes a **Job Match** feature that ranks
jobs by how many of their required skills you have.

Built for COP4751 (Advanced Database Management) with MySQL, Python/Flask, and
HTML/CSS (Bootstrap).

## Features

- **Dashboard**: totals, applications by status, response rate, jobs per company,
  average salary by industry, jobs by type, and recent applications
- **Companies, Jobs, Applications, Contacts**: list, detail view, add, edit, and
  delete (with a confirmation prompt) for all four tables, with form validation
- **Job Match**: enter your skills and see jobs ranked by match percentage, with the
  skills you have and the ones you are missing
- **JSON columns**: `jobs.requirements` (skills, experience, education, remote) and
  `applications.interview_data` (rounds, interviewers, questions, feedback, rating, offer)

## Setup

You need Python 3 and MySQL Server 8 running on your computer.

1. **Clone the repo and install the dependencies**

       git clone https://github.com/Jcalarino/job-application-tracker.git
       cd job-application-tracker
       pip install -r requirements.txt

2. **Create the database.** In MySQL Workbench (or the `mysql` command line), open and
   run `schema.sql`, then `sample_data.sql`. This creates a database named
   `job_tracker_app` with four tables and loads sample data (6 companies, 12 jobs,
   7 applications, 7 contacts).

       mysql -u root -p < schema.sql
       mysql -u root -p < sample_data.sql

3. **Add your MySQL login.** Copy `config.example.py` to `config.py` and put in your
   MySQL user and password (`config.py` is ignored by Git so it stays private).

       copy config.example.py config.py        (Windows)
       cp config.example.py config.py          (macOS/Linux)

4. **Run the app**

       python app.py

   Then open http://127.0.0.1:5000 in your browser.

`sample_data.sql` can be re-run at any time to reset the data. `schema.sql` drops and
rebuilds the four tables, so re-running it erases their contents.

## Database design

| Table | Purpose | Key columns |
|---|---|---|
| `companies` | Employers | `company_id` (PK), `company_name`, `industry`, `city`, `state` |
| `jobs` | Job postings | `job_id` (PK), `company_id` (FK), `job_type` (ENUM), salary range, `requirements` (JSON) |
| `applications` | Your applications | `application_id` (PK), `job_id` (FK), `status` (ENUM), `interview_data` (JSON) |
| `contacts` | People at companies | `contact_id` (PK), `company_id` (FK), `contact_name`, `email`, `linkedin_url` |

- One company has many jobs and many contacts; one job has many applications.
- Foreign keys use `ON DELETE CASCADE`, so deleting a company also removes its jobs,
  contacts, and applications (the app warns before it does this).
- Indexes: `idx_job_title`, `idx_company_type` (company, job type), `idx_app_status`,
  and `idx_company_industry`.
- JSON is used for flexible, per-record data that varies (skills lists, interview
  notes). Data that is filtered, joined, or sorted on stays in regular columns.

## How Job Match works

1. Each job stores its `required_skills` in the `requirements` JSON column.
2. You enter your skills; matching ignores upper/lower case.
3. For each job: **match % = skills you have / required skills**, rounded.
   Preferred skills are shown as a bonus but do not change the percentage.
4. Jobs are ranked best first. Each result lists the skills you have and the ones you
   are missing. Jobs where you match nothing are hidden.

The scoring logic is in `matching.py` (no database code), with unit tests:

    python test_matching.py

## Project structure

    app.py               Flask routes and form validation
    database.py          Database connection and query helpers (parameterized queries)
    matching.py          Job Match scoring logic
    test_matching.py     Unit tests for matching.py
    config.example.py    Template for config.py (your private DB login)
    schema.sql           Creates the database and tables
    sample_data.sql      Loads demo data
    templates/           HTML pages (Jinja2 + Bootstrap)
    static/style.css     Custom styles
    practice/            Assignment 5 practice scripts
    AI_USAGE.md          How GenAI tools were used
    requirements.txt     Python dependencies

## Why MySQL

The data has clear relationships (companies, jobs, applications, contacts), needs
integrity (foreign keys and cascading deletes), and has a consistent structure. JSON
columns cover the flexible parts, so the app combines relational and document-style
storage in one database.

## Security notes

- All SQL uses `%s` parameters, never string concatenation, to prevent SQL injection.
- Jinja2 escapes all displayed text, and links are only created for `http://` or
  `https://` addresses.
- The database password lives in `config.py`, which is not committed.
