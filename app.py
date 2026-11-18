import json
import re
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

from database import fetch_all, fetch_one, execute
from matching import parse_skills, rank_jobs, collect_skills

app = Flask(__name__)
app.secret_key = 'change-this-to-any-random-text'  # needed for flash messages


@app.template_filter('web_url')
def web_url(value):
    """Make a stored website safe to use as a link.

    'www.site.com' -> 'https://www.site.com'; anything that is not a plain
    web address (like a javascript: link) becomes '' so templates skip the link.
    """
    if not value:
        return ''
    value = value.strip()
    if re.match(r'^https?://', value, re.IGNORECASE):
        return value
    if '://' in value or re.match(r'^(javascript|data|vbscript):', value, re.IGNORECASE):
        return ''
    return 'https://' + value


# ------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------
STATUS_COLORS = {
    'Applied': 'secondary',
    'Screening': 'info',
    'Interview': 'primary',
    'Offer': 'success',
    'Rejected': 'danger',
    'Withdrawn': 'dark',
}


def add_bar_widths(rows, key):
    """Give each row a 'width' (0-100) relative to the biggest value, for CSS bar charts."""
    biggest = max([r[key] for r in rows] or [0]) or 1
    for row in rows:
        row['width'] = int(100 * row[key] / biggest)
    return rows


@app.route('/')
def dashboard():
    stats = {
        'companies': fetch_one('SELECT COUNT(*) AS n FROM companies')['n'],
        'jobs': fetch_one('SELECT COUNT(*) AS n FROM jobs')['n'],
        'applications': fetch_one('SELECT COUNT(*) AS n FROM applications')['n'],
        'contacts': fetch_one('SELECT COUNT(*) AS n FROM contacts')['n'],
    }

    # Applications by status (every status is listed, even with zero)
    by_status = {row['status']: row['n'] for row in fetch_all(
        'SELECT status, COUNT(*) AS n FROM applications GROUP BY status')}
    status_counts = add_bar_widths([
        {'status': s, 'n': by_status.get(s, 0), 'color': STATUS_COLORS[s]}
        for s in APPLICATION_STATUSES], 'n')

    # Response rate: share of applications that moved past "Applied"
    total_apps = stats['applications']
    responded = total_apps - by_status.get('Applied', 0)
    response_rate = int(100 * responded / total_apps + 0.5) if total_apps else 0

    jobs_per_company = add_bar_widths(fetch_all('''
        SELECT c.company_name, COUNT(j.job_id) AS n
        FROM companies c
        LEFT JOIN jobs j ON c.company_id = j.company_id
        GROUP BY c.company_id, c.company_name
        ORDER BY n DESC, c.company_name
    '''), 'n')

    salary_rows = fetch_all('''
        SELECT c.industry, COUNT(*) AS n,
               ROUND(AVG(j.salary_min)) AS avg_min, ROUND(AVG(j.salary_max)) AS avg_max
        FROM companies c
        JOIN jobs j ON c.company_id = j.company_id
        WHERE j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL AND c.industry IS NOT NULL
        GROUP BY c.industry
        ORDER BY avg_max DESC
    ''')
    for row in salary_rows:
        row['avg_min'] = int(row['avg_min'])
        row['avg_max'] = int(row['avg_max'])
    salary_by_industry = add_bar_widths(salary_rows, 'avg_max')

    jobs_by_type = add_bar_widths(fetch_all('''
        SELECT job_type, COUNT(*) AS n
        FROM jobs
        WHERE job_type IS NOT NULL
        GROUP BY job_type
        ORDER BY n DESC
    '''), 'n')

    recent = fetch_all('''
        SELECT a.application_id, a.application_date, a.status, j.job_title, c.company_name
        FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY a.application_date DESC, a.application_id DESC
        LIMIT 5
    ''')

    return render_template('dashboard.html', stats=stats, status_counts=status_counts,
                           response_rate=response_rate, responded=responded,
                           jobs_per_company=jobs_per_company,
                           salary_by_industry=salary_by_industry,
                           jobs_by_type=jobs_by_type, recent=recent,
                           offers=by_status.get('Offer', 0))


# ------------------------------------------------------------
# Companies: list / add / edit / delete
# ------------------------------------------------------------
def read_company_form():
    """Pull the company fields from the submitted form and validate them."""
    data = {
        'company_name': request.form.get('company_name', '').strip(),
        'industry': request.form.get('industry', '').strip(),
        'website': request.form.get('website', '').strip(),
        'city': request.form.get('city', '').strip(),
        'state': request.form.get('state', '').strip(),
        'notes': request.form.get('notes', '').strip(),
    }
    errors = []
    if not data['company_name']:
        errors.append('Company name is required.')
    if len(data['company_name']) > 100:
        errors.append('Company name must be 100 characters or fewer.')
    if len(data['industry']) > 50:
        errors.append('Industry must be 50 characters or fewer.')
    if len(data['website']) > 200:
        errors.append('Website must be 200 characters or fewer.')
    if len(data['city']) > 50 or len(data['state']) > 50:
        errors.append('City and state must be 50 characters or fewer.')
    # Empty optional fields are stored as NULL instead of ''
    for key in ('industry', 'website', 'city', 'state', 'notes'):
        if data[key] == '':
            data[key] = None
    return data, errors


@app.route('/companies')
def companies():
    rows = fetch_all('''
        SELECT c.*, COUNT(j.job_id) AS job_count
        FROM companies c
        LEFT JOIN jobs j ON c.company_id = j.company_id
        GROUP BY c.company_id
        ORDER BY c.company_name
    ''')
    return render_template('companies.html', companies=rows)


@app.route('/companies/<int:company_id>')
def company_detail(company_id):
    company = fetch_one('SELECT * FROM companies WHERE company_id = %s', (company_id,))
    if company is None:
        flash('Company not found.', 'warning')
        return redirect(url_for('companies'))
    company_jobs = fetch_all('''
        SELECT j.job_id, j.job_title, j.job_type, j.salary_min, j.salary_max, j.date_posted,
               COUNT(a.application_id) AS app_count
        FROM jobs j
        LEFT JOIN applications a ON a.job_id = j.job_id
        WHERE j.company_id = %s
        GROUP BY j.job_id
        ORDER BY j.date_posted DESC, j.job_title
    ''', (company_id,))
    company_contacts = fetch_all('''
        SELECT contact_id, contact_name, title, email, phone
        FROM contacts WHERE company_id = %s ORDER BY contact_name
    ''', (company_id,))
    return render_template('company_detail.html', company=company,
                           jobs=company_jobs, contacts=company_contacts)


@app.route('/companies/add', methods=['GET', 'POST'])
def add_company():
    if request.method == 'POST':
        data, errors = read_company_form()
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('company_form.html', company=data, mode='add')
        try:
            execute('''
                INSERT INTO companies (company_name, industry, website, city, state, notes)
                VALUES (%(company_name)s, %(industry)s, %(website)s, %(city)s, %(state)s, %(notes)s)
            ''', data)
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
            return render_template('company_form.html', company=data, mode='add')
        flash(f"Added {data['company_name']}", 'success')
        return redirect(url_for('companies'))
    return render_template('company_form.html', company={}, mode='add')


@app.route('/companies/<int:company_id>/edit', methods=['GET', 'POST'])
def edit_company(company_id):
    existing = fetch_one('SELECT * FROM companies WHERE company_id = %s', (company_id,))
    if existing is None:
        flash('Company not found.', 'warning')
        return redirect(url_for('companies'))

    if request.method == 'POST':
        data, errors = read_company_form()
        if errors:
            for e in errors:
                flash(e, 'danger')
            data['company_id'] = company_id
            return render_template('company_form.html', company=data, mode='edit')
        data['company_id'] = company_id
        try:
            execute('''
                UPDATE companies
                SET company_name = %(company_name)s, industry = %(industry)s,
                    website = %(website)s, city = %(city)s, state = %(state)s,
                    notes = %(notes)s
                WHERE company_id = %(company_id)s
            ''', data)
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
            return render_template('company_form.html', company=data, mode='edit')
        flash(f"Updated {data['company_name']}", 'success')
        return redirect(url_for('companies'))

    return render_template('company_form.html', company=existing, mode='edit')


@app.route('/companies/<int:company_id>/delete', methods=['POST'])
def delete_company(company_id):
    existing = fetch_one('SELECT company_name FROM companies WHERE company_id = %s', (company_id,))
    if existing is None:
        flash('Company not found.', 'warning')
    else:
        try:
            # ON DELETE CASCADE also removes this company's jobs, contacts and applications
            execute('DELETE FROM companies WHERE company_id = %s', (company_id,))
            flash(f"Deleted {existing['company_name']} and everything linked to it.", 'success')
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
    return redirect(url_for('companies'))


# ------------------------------------------------------------
# Jobs: list / add / edit / delete
# The requirements JSON column is built from simple form fields.
# ------------------------------------------------------------
JOB_TYPES = ['Full-time', 'Part-time', 'Contract', 'Internship']


# Skill lists are parsed the same way for the job form and for Job Match
split_skills = parse_skills


def load_requirements(raw):
    """MySQL hands JSON back as text; turn it into a dict (empty dict if missing/bad)."""
    if raw is None:
        return {}
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode()
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return {}
    return raw if isinstance(raw, dict) else {}


def parse_whole_number(text, label, errors):
    """Return an int >= 0, None if blank, and add an error if invalid."""
    text = (text or '').strip()
    if text == '':
        return None
    if not text.isdigit():
        errors.append(f'{label} must be a whole number (0 or more).')
        return None
    return int(text)


def job_to_form(row):
    """Turn a jobs row into the plain values the form displays."""
    req = load_requirements(row.get('requirements'))
    posted = row.get('date_posted')
    return {
        'job_id': row.get('job_id'),
        'company_id': row.get('company_id'),
        'job_title': row.get('job_title') or '',
        'job_type': row.get('job_type') or '',
        'salary_min': '' if row.get('salary_min') is None else row['salary_min'],
        'salary_max': '' if row.get('salary_max') is None else row['salary_max'],
        'job_url': row.get('job_url') or '',
        'date_posted': posted.isoformat() if posted else '',
        'required_skills': ', '.join(req.get('required_skills', [])),
        'preferred_skills': ', '.join(req.get('preferred_skills', [])),
        'experience_years': '' if req.get('experience_years') is None else req['experience_years'],
        'education': req.get('education', ''),
        'remote_option': bool(req.get('remote_option', False)),
    }


def read_job_form(existing_requirements=None):
    """Validate the submitted job form. Returns (db_values, form_values, errors)."""
    f = request.form
    errors = []

    company_id = f.get('company_id', '').strip()
    job_title = f.get('job_title', '').strip()
    job_type = f.get('job_type', '').strip()
    job_url = f.get('job_url', '').strip()
    date_posted = f.get('date_posted', '').strip()
    education = f.get('education', '').strip()
    remote = 'remote_option' in f

    # Company must be chosen and must exist
    if not company_id.isdigit() or fetch_one(
            'SELECT company_id FROM companies WHERE company_id = %s', (company_id,)) is None:
        errors.append('Please choose a company.')
    if not job_title:
        errors.append('Job title is required.')
    if len(job_title) > 100:
        errors.append('Job title must be 100 characters or fewer.')
    if job_type and job_type not in JOB_TYPES:
        errors.append('Please choose a valid job type.')
    if len(job_url) > 300:
        errors.append('Job URL must be 300 characters or fewer.')
    elif job_url and not re.match(r'^https?://', job_url, re.IGNORECASE):
        errors.append('Job URL must start with http:// or https://')

    salary_min = parse_whole_number(f.get('salary_min'), 'Minimum salary', errors)
    salary_max = parse_whole_number(f.get('salary_max'), 'Maximum salary', errors)
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        errors.append('Minimum salary cannot be higher than maximum salary.')

    experience = parse_whole_number(f.get('experience_years'), 'Years of experience', errors)

    if date_posted:
        try:
            datetime.strptime(date_posted, '%Y-%m-%d')
        except ValueError:
            errors.append('Date posted must be a valid date.')

    # Build the JSON, keeping any extra keys the job already had
    requirements = dict(existing_requirements or {})
    requirements['required_skills'] = split_skills(f.get('required_skills'))
    requirements['preferred_skills'] = split_skills(f.get('preferred_skills'))
    requirements['remote_option'] = remote
    if experience is not None:
        requirements['experience_years'] = experience
    else:
        requirements.pop('experience_years', None)
    if education:
        requirements['education'] = education
    else:
        requirements.pop('education', None)

    db_values = {
        'company_id': int(company_id) if company_id.isdigit() else None,
        'job_title': job_title,
        'job_type': job_type or None,
        'salary_min': salary_min,
        'salary_max': salary_max,
        'job_url': job_url or None,
        'date_posted': date_posted or None,
        'requirements': json.dumps(requirements),
    }
    form_values = {
        'company_id': int(company_id) if company_id.isdigit() else None,
        'job_title': job_title,
        'job_type': job_type,
        'salary_min': f.get('salary_min', ''),
        'salary_max': f.get('salary_max', ''),
        'job_url': job_url,
        'date_posted': date_posted,
        'required_skills': f.get('required_skills', ''),
        'preferred_skills': f.get('preferred_skills', ''),
        'experience_years': f.get('experience_years', ''),
        'education': education,
        'remote_option': remote,
    }
    return db_values, form_values, errors


def company_choices():
    return fetch_all('SELECT company_id, company_name FROM companies ORDER BY company_name')


@app.route('/jobs')
def jobs():
    rows = fetch_all('''
        SELECT j.*, c.company_name, COUNT(a.application_id) AS app_count
        FROM jobs j
        JOIN companies c ON j.company_id = c.company_id
        LEFT JOIN applications a ON a.job_id = j.job_id
        GROUP BY j.job_id, c.company_name
        ORDER BY j.date_posted DESC, j.job_title
    ''')
    for row in rows:
        row['required'] = load_requirements(row['requirements']).get('required_skills', [])
    return render_template('jobs.html', jobs=rows)


@app.route('/jobs/<int:job_id>')
def job_detail(job_id):
    job = fetch_one('''
        SELECT j.*, c.company_name
        FROM jobs j JOIN companies c ON j.company_id = c.company_id
        WHERE j.job_id = %s
    ''', (job_id,))
    if job is None:
        flash('Job not found.', 'warning')
        return redirect(url_for('jobs'))
    job_applications = fetch_all('''
        SELECT application_id, application_date, status, resume_version
        FROM applications WHERE job_id = %s
        ORDER BY application_date DESC, application_id DESC
    ''', (job_id,))
    return render_template('job_detail.html', job=job,
                           requirements=load_requirements(job['requirements']),
                           applications=job_applications)


@app.route('/jobs/add', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':
        data, form, errors = read_job_form()
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('job_form.html', job=form, mode='add',
                                   companies=company_choices(), job_types=JOB_TYPES)
        try:
            execute('''
                INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max,
                                  job_url, date_posted, requirements)
                VALUES (%(company_id)s, %(job_title)s, %(job_type)s, %(salary_min)s,
                        %(salary_max)s, %(job_url)s, %(date_posted)s, %(requirements)s)
            ''', data)
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
            return render_template('job_form.html', job=form, mode='add',
                                   companies=company_choices(), job_types=JOB_TYPES)
        flash(f"Added job {data['job_title']}", 'success')
        return redirect(url_for('jobs'))

    blank = job_to_form({})
    preselect = request.args.get('company_id', '')
    blank['company_id'] = int(preselect) if preselect.isdigit() else None
    return render_template('job_form.html', job=blank, mode='add',
                           companies=company_choices(), job_types=JOB_TYPES)


@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    existing = fetch_one('SELECT * FROM jobs WHERE job_id = %s', (job_id,))
    if existing is None:
        flash('Job not found.', 'warning')
        return redirect(url_for('jobs'))

    if request.method == 'POST':
        data, form, errors = read_job_form(load_requirements(existing['requirements']))
        form['job_id'] = job_id
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('job_form.html', job=form, mode='edit',
                                   companies=company_choices(), job_types=JOB_TYPES)
        data['job_id'] = job_id
        try:
            execute('''
                UPDATE jobs
                SET company_id = %(company_id)s, job_title = %(job_title)s,
                    job_type = %(job_type)s, salary_min = %(salary_min)s,
                    salary_max = %(salary_max)s, job_url = %(job_url)s,
                    date_posted = %(date_posted)s, requirements = %(requirements)s
                WHERE job_id = %(job_id)s
            ''', data)
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
            return render_template('job_form.html', job=form, mode='edit',
                                   companies=company_choices(), job_types=JOB_TYPES)
        flash(f"Updated job {data['job_title']}", 'success')
        return redirect(url_for('jobs'))

    return render_template('job_form.html', job=job_to_form(existing), mode='edit',
                           companies=company_choices(), job_types=JOB_TYPES)


@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    existing = fetch_one('SELECT job_title FROM jobs WHERE job_id = %s', (job_id,))
    if existing is None:
        flash('Job not found.', 'warning')
    else:
        try:
            # ON DELETE CASCADE also removes the applications for this job
            execute('DELETE FROM jobs WHERE job_id = %s', (job_id,))
            flash(f"Deleted job {existing['job_title']} and its applications.", 'success')
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
    return redirect(url_for('jobs'))


# ------------------------------------------------------------
# Applications: list (with status filter) / detail / add / edit / delete
# The interview_data JSON column is built from simple form fields.
# ------------------------------------------------------------
APPLICATION_STATUSES = ['Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn']


def application_to_form(row):
    """Turn an applications row into the plain values the form displays."""
    data = load_requirements(row.get('interview_data'))
    applied = row.get('application_date')
    return {
        'application_id': row.get('application_id'),
        'job_id': row.get('job_id'),
        'application_date': applied.isoformat() if applied else '',
        'status': row.get('status') or 'Applied',
        'resume_version': row.get('resume_version') or '',
        'cover_letter_sent': bool(row.get('cover_letter_sent')),
        'interview_rounds': '' if data.get('interview_rounds') is None else data['interview_rounds'],
        'interviewers': ', '.join(data.get('interviewers', [])),
        'technical_questions': ', '.join(data.get('technical_questions', [])),
        'feedback': data.get('feedback', ''),
        'next_steps': data.get('next_steps', ''),
        'rating': '' if data.get('rating') is None else data['rating'],
        'offer_amount': '' if data.get('offer_amount') is None else data['offer_amount'],
    }


def read_application_form(existing_interview=None):
    """Validate the submitted application form. Returns (db_values, form_values, errors)."""
    f = request.form
    errors = []

    job_id = f.get('job_id', '').strip()
    application_date = f.get('application_date', '').strip()
    status = f.get('status', '').strip()
    resume_version = f.get('resume_version', '').strip()
    cover_letter = 'cover_letter_sent' in f

    if not job_id.isdigit() or fetch_one(
            'SELECT job_id FROM jobs WHERE job_id = %s', (job_id,)) is None:
        errors.append('Please choose a job.')
    if not application_date:
        errors.append('Application date is required.')
    else:
        try:
            datetime.strptime(application_date, '%Y-%m-%d')
        except ValueError:
            errors.append('Application date must be a valid date.')
    if status not in APPLICATION_STATUSES:
        errors.append('Please choose a valid status.')
    if len(resume_version) > 50:
        errors.append('Resume version must be 50 characters or fewer.')

    rounds = parse_whole_number(f.get('interview_rounds'), 'Interview rounds', errors)
    rating = parse_whole_number(f.get('rating'), 'Rating', errors)
    if rating is not None and not 1 <= rating <= 5:
        errors.append('Rating must be between 1 and 5.')
    offer = parse_whole_number(f.get('offer_amount'), 'Offer amount', errors)

    # Build the JSON, keeping any extra keys the record already had
    interview = dict(existing_interview or {})

    def put(key, value):
        if value is None or value == '' or value == []:
            interview.pop(key, None)
        else:
            interview[key] = value

    put('interview_rounds', rounds)
    put('interviewers', split_skills(f.get('interviewers')))
    put('technical_questions', split_skills(f.get('technical_questions')))
    put('feedback', f.get('feedback', '').strip())
    put('next_steps', f.get('next_steps', '').strip())
    put('rating', rating)
    put('offer_amount', offer)

    db_values = {
        'job_id': int(job_id) if job_id.isdigit() else None,
        'application_date': application_date or None,
        'status': status,
        'resume_version': resume_version or None,
        'cover_letter_sent': cover_letter,
        # Stay NULL when there are no interview notes at all
        'interview_data': json.dumps(interview) if interview else None,
    }
    form_values = {
        'job_id': int(job_id) if job_id.isdigit() else None,
        'application_date': application_date,
        'status': status,
        'resume_version': resume_version,
        'cover_letter_sent': cover_letter,
        'interview_rounds': f.get('interview_rounds', ''),
        'interviewers': f.get('interviewers', ''),
        'technical_questions': f.get('technical_questions', ''),
        'feedback': f.get('feedback', ''),
        'next_steps': f.get('next_steps', ''),
        'rating': f.get('rating', ''),
        'offer_amount': f.get('offer_amount', ''),
    }
    return db_values, form_values, errors


def job_choices():
    return fetch_all('''
        SELECT j.job_id, j.job_title, c.company_name
        FROM jobs j JOIN companies c ON j.company_id = c.company_id
        ORDER BY c.company_name, j.job_title
    ''')


def render_application_form(form, mode):
    return render_template('application_form.html', application=form, mode=mode,
                           jobs=job_choices(), statuses=APPLICATION_STATUSES)


@app.route('/applications')
def applications():
    status = request.args.get('status', '').strip()
    sql = '''
        SELECT a.*, j.job_title, c.company_name
        FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
    '''
    params = ()
    if status in APPLICATION_STATUSES:
        sql += ' WHERE a.status = %s'
        params = (status,)
    sql += ' ORDER BY a.application_date DESC, a.application_id DESC'
    rows = fetch_all(sql, params)
    for row in rows:
        row['interview'] = load_requirements(row['interview_data'])
    return render_template('applications.html', applications=rows,
                           statuses=APPLICATION_STATUSES,
                           selected=status if status in APPLICATION_STATUSES else '')


@app.route('/applications/<int:application_id>')
def application_detail(application_id):
    row = fetch_one('''
        SELECT a.*, j.job_title, j.company_id, c.company_name
        FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        WHERE a.application_id = %s
    ''', (application_id,))
    if row is None:
        flash('Application not found.', 'warning')
        return redirect(url_for('applications'))
    return render_template('application_detail.html', a=row,
                           interview=load_requirements(row['interview_data']))


@app.route('/applications/add', methods=['GET', 'POST'])
def add_application():
    if request.method == 'POST':
        data, form, errors = read_application_form()
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_application_form(form, 'add')
        try:
            execute('''
                INSERT INTO applications (job_id, application_date, status, resume_version,
                                          cover_letter_sent, interview_data)
                VALUES (%(job_id)s, %(application_date)s, %(status)s, %(resume_version)s,
                        %(cover_letter_sent)s, %(interview_data)s)
            ''', data)
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
            return render_application_form(form, 'add')
        flash('Application added', 'success')
        return redirect(url_for('applications'))

    blank = application_to_form({})
    blank['application_date'] = datetime.today().strftime('%Y-%m-%d')
    preselect = request.args.get('job_id', '')
    blank['job_id'] = int(preselect) if preselect.isdigit() else None
    return render_application_form(blank, 'add')


@app.route('/applications/<int:application_id>/edit', methods=['GET', 'POST'])
def edit_application(application_id):
    existing = fetch_one('SELECT * FROM applications WHERE application_id = %s', (application_id,))
    if existing is None:
        flash('Application not found.', 'warning')
        return redirect(url_for('applications'))

    if request.method == 'POST':
        data, form, errors = read_application_form(load_requirements(existing['interview_data']))
        form['application_id'] = application_id
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_application_form(form, 'edit')
        data['application_id'] = application_id
        try:
            execute('''
                UPDATE applications
                SET job_id = %(job_id)s, application_date = %(application_date)s,
                    status = %(status)s, resume_version = %(resume_version)s,
                    cover_letter_sent = %(cover_letter_sent)s, interview_data = %(interview_data)s
                WHERE application_id = %(application_id)s
            ''', data)
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
            return render_application_form(form, 'edit')
        flash('Application updated', 'success')
        return redirect(url_for('applications'))

    return render_application_form(application_to_form(existing), 'edit')


@app.route('/applications/<int:application_id>/delete', methods=['POST'])
def delete_application(application_id):
    existing = fetch_one('SELECT application_id FROM applications WHERE application_id = %s',
                         (application_id,))
    if existing is None:
        flash('Application not found.', 'warning')
    else:
        try:
            execute('DELETE FROM applications WHERE application_id = %s', (application_id,))
            flash('Application deleted.', 'success')
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
    return redirect(url_for('applications'))


# ------------------------------------------------------------
# Contacts: list (with company filter) / add / edit / delete
# ------------------------------------------------------------
EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_PATTERN = re.compile(r'^[0-9 ()+.\-]+$')


def read_contact_form():
    """Validate the submitted contact form. Returns (values, errors)."""
    f = request.form
    errors = []
    data = {
        'company_id': f.get('company_id', '').strip(),
        'contact_name': f.get('contact_name', '').strip(),
        'title': f.get('title', '').strip(),
        'email': f.get('email', '').strip(),
        'phone': f.get('phone', '').strip(),
        'linkedin_url': f.get('linkedin_url', '').strip(),
        'notes': f.get('notes', '').strip(),
    }

    if not data['company_id'].isdigit() or fetch_one(
            'SELECT company_id FROM companies WHERE company_id = %s', (data['company_id'],)) is None:
        errors.append('Please choose a company.')
    if not data['contact_name']:
        errors.append('Contact name is required.')
    if len(data['contact_name']) > 100:
        errors.append('Contact name must be 100 characters or fewer.')
    if len(data['title']) > 100:
        errors.append('Title must be 100 characters or fewer.')
    if data['email']:
        if len(data['email']) > 100:
            errors.append('Email must be 100 characters or fewer.')
        elif not EMAIL_PATTERN.match(data['email']):
            errors.append('Please enter a valid email address (like name@company.com).')
    if data['phone']:
        if len(data['phone']) > 20:
            errors.append('Phone must be 20 characters or fewer.')
        elif not PHONE_PATTERN.match(data['phone']):
            errors.append('Phone can only contain digits, spaces, and + - ( ) .')
    if data['linkedin_url']:
        if len(data['linkedin_url']) > 200:
            errors.append('LinkedIn URL must be 200 characters or fewer.')
        elif not re.match(r'^https?://', data['linkedin_url'], re.IGNORECASE):
            errors.append('LinkedIn URL must start with http:// or https://')

    for key in ('title', 'email', 'phone', 'linkedin_url', 'notes'):
        if data[key] == '':
            data[key] = None
    data['company_id'] = int(data['company_id']) if data['company_id'].isdigit() else None
    return data, errors


def render_contact_form(contact, mode):
    return render_template('contact_form.html', contact=contact, mode=mode,
                           companies=company_choices())


@app.route('/contacts')
def contacts():
    company_id = request.args.get('company_id', '').strip()
    sql = '''
        SELECT ct.*, c.company_name
        FROM contacts ct
        JOIN companies c ON ct.company_id = c.company_id
    '''
    params = ()
    if company_id.isdigit():
        sql += ' WHERE ct.company_id = %s'
        params = (int(company_id),)
    sql += ' ORDER BY ct.contact_name'
    rows = fetch_all(sql, params)
    return render_template('contacts.html', contacts=rows, companies=company_choices(),
                           selected=int(company_id) if company_id.isdigit() else None)


@app.route('/contacts/<int:contact_id>')
def contact_detail(contact_id):
    contact = fetch_one('''
        SELECT ct.*, c.company_name
        FROM contacts ct JOIN companies c ON ct.company_id = c.company_id
        WHERE ct.contact_id = %s
    ''', (contact_id,))
    if contact is None:
        flash('Contact not found.', 'warning')
        return redirect(url_for('contacts'))
    return render_template('contact_detail.html', contact=contact)


@app.route('/contacts/add', methods=['GET', 'POST'])
def add_contact():
    if request.method == 'POST':
        data, errors = read_contact_form()
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_contact_form(data, 'add')
        try:
            execute('''
                INSERT INTO contacts (company_id, contact_name, title, email, phone,
                                      linkedin_url, notes)
                VALUES (%(company_id)s, %(contact_name)s, %(title)s, %(email)s, %(phone)s,
                        %(linkedin_url)s, %(notes)s)
            ''', data)
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
            return render_contact_form(data, 'add')
        flash(f"Added contact {data['contact_name']}", 'success')
        return redirect(url_for('contacts'))

    preselect = request.args.get('company_id', '')
    return render_contact_form(
        {'company_id': int(preselect) if preselect.isdigit() else None}, 'add')


@app.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
def edit_contact(contact_id):
    existing = fetch_one('SELECT * FROM contacts WHERE contact_id = %s', (contact_id,))
    if existing is None:
        flash('Contact not found.', 'warning')
        return redirect(url_for('contacts'))

    if request.method == 'POST':
        data, errors = read_contact_form()
        data['contact_id'] = contact_id
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_contact_form(data, 'edit')
        try:
            execute('''
                UPDATE contacts
                SET company_id = %(company_id)s, contact_name = %(contact_name)s,
                    title = %(title)s, email = %(email)s, phone = %(phone)s,
                    linkedin_url = %(linkedin_url)s, notes = %(notes)s
                WHERE contact_id = %(contact_id)s
            ''', data)
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
            return render_contact_form(data, 'edit')
        flash(f"Updated contact {data['contact_name']}", 'success')
        return redirect(url_for('contacts'))

    return render_contact_form(existing, 'edit')


@app.route('/contacts/<int:contact_id>/delete', methods=['POST'])
def delete_contact(contact_id):
    existing = fetch_one('SELECT contact_name FROM contacts WHERE contact_id = %s', (contact_id,))
    if existing is None:
        flash('Contact not found.', 'warning')
    else:
        try:
            execute('DELETE FROM contacts WHERE contact_id = %s', (contact_id,))
            flash(f"Deleted contact {existing['contact_name']}.", 'success')
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'danger')
    return redirect(url_for('contacts'))


# ------------------------------------------------------------
# Job Match: enter your skills, see jobs ranked by match percentage
# (the scoring itself lives in matching.py)
# ------------------------------------------------------------
@app.route('/job-match')
def job_match():
    raw = request.args.get('skills', '').strip()
    user_skills = parse_skills(raw[:500])[:30]

    rows = fetch_all('''
        SELECT j.job_id, j.job_title, j.job_type, j.requirements, c.company_name
        FROM jobs j
        JOIN companies c ON j.company_id = c.company_id
    ''')
    jobs_for_matching = []
    for row in rows:
        requirements = load_requirements(row['requirements'])
        jobs_for_matching.append({
            'job_id': row['job_id'],
            'job_title': row['job_title'],
            'job_type': row['job_type'],
            'company_name': row['company_name'],
            'required_skills': requirements.get('required_skills', []),
            'preferred_skills': requirements.get('preferred_skills', []),
        })

    results, skipped, zero_match = None, 0, 0
    if user_skills:
        results, skipped, zero_match = rank_jobs(jobs_for_matching, user_skills)

    return render_template('job_match.html',
                           skills_text=', '.join(user_skills),
                           user_skills=user_skills,
                           results=results,
                           skipped=skipped,
                           zero_match=zero_match,
                           known_skills=collect_skills(jobs_for_matching))


if __name__ == '__main__':
    app.run(debug=True)
