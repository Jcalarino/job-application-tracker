"""Job Match: rank jobs by how many of their required skills the user has.

This file has no database or Flask code, so the logic is easy to test
(see test_matching.py).

Rules:
  * Skills are compared case-insensitively ("python" matches "Python").
  * Percent = skills you have / required skills for that job, rounded.
  * Preferred skills are shown as a bonus but do not change the percent.
  * Jobs with no required skills listed are skipped (nothing to score),
    and jobs where you match none of the required skills are left out.
"""


def _unique(skills):
    """Trim, collapse extra spaces, drop blanks and case-insensitive duplicates."""
    seen, result = set(), []
    for skill in skills or []:
        skill = ' '.join(str(skill).split())
        key = skill.lower()
        if skill and key not in seen:
            seen.add(key)
            result.append(skill)
    return result


def parse_skills(text):
    """'Python, SQL ,python' -> ['Python', 'SQL']"""
    return _unique((text or '').replace('\n', ',').split(','))


def rank_jobs(jobs, user_skills):
    """Score every job against the user's skills.

    jobs: list of dicts with job_title, required_skills and preferred_skills
          (plus any other fields you want carried through, like job_id).
    Returns (ranked, skipped_count, zero_match_count) where ranked is
    best match first.
    """
    have = {skill.lower() for skill in user_skills}
    ranked = []
    skipped = 0
    zero_match = 0

    for job in jobs:
        required = _unique(job.get('required_skills'))
        if not required:
            skipped += 1
            continue

        matched = [s for s in required if s.lower() in have]
        if not matched:
            zero_match += 1
            continue

        preferred = _unique(job.get('preferred_skills'))
        result = dict(job)
        result.update(
            matched=matched,
            missing=[s for s in required if s.lower() not in have],
            total=len(required),
            matched_count=len(matched),
            percent=int(100 * len(matched) / len(required) + 0.5),
            preferred_matched=[s for s in preferred if s.lower() in have],
            preferred_total=len(preferred),
        )
        ranked.append(result)

    # Best percentage first; ties go to the job with more matched skills, then by title
    ranked.sort(key=lambda r: (-r['matched_count'] / r['total'],
                               -r['matched_count'],
                               r['job_title'].lower()))
    return ranked, skipped, zero_match


def collect_skills(jobs):
    """All distinct required skills across jobs, alphabetical (for the suggestion chips)."""
    everything = []
    for job in jobs:
        everything.extend(job.get('required_skills') or [])
    return sorted(_unique(everything), key=str.lower)
