"""Tests for the Job Match algorithm. Run with:  python test_matching.py"""
import unittest

from matching import parse_skills, rank_jobs, collect_skills

JOBS = [
    {'job_id': 1, 'job_title': 'Software Developer',
     'required_skills': ['Python', 'SQL', 'Flask'], 'preferred_skills': ['Docker']},
    {'job_id': 2, 'job_title': 'Data Analyst',
     'required_skills': ['SQL', 'Excel', 'Tableau'], 'preferred_skills': ['Python']},
    {'job_id': 3, 'job_title': 'Cloud Engineer',
     'required_skills': ['AWS', 'Linux'], 'preferred_skills': []},
    {'job_id': 4, 'job_title': 'No Requirements Listed',
     'required_skills': [], 'preferred_skills': []},
]


class ParseSkillsTests(unittest.TestCase):
    def test_trims_and_removes_duplicates_ignoring_case(self):
        self.assertEqual(parse_skills(' Python, SQL ,python,, Flask '), ['Python', 'SQL', 'Flask'])

    def test_blank_input(self):
        self.assertEqual(parse_skills(''), [])
        self.assertEqual(parse_skills(None), [])

    def test_collapses_inner_spaces(self):
        self.assertEqual(parse_skills('Machine   Learning'), ['Machine Learning'])


class RankJobsTests(unittest.TestCase):
    def test_full_match_is_100_percent(self):
        ranked, _, _ = rank_jobs(JOBS, ['Python', 'SQL', 'Flask'])
        self.assertEqual(ranked[0]['job_title'], 'Software Developer')
        self.assertEqual(ranked[0]['percent'], 100)
        self.assertEqual(ranked[0]['missing'], [])

    def test_partial_match_lists_missing_skills(self):
        ranked, _, _ = rank_jobs(JOBS, ['Python', 'SQL', 'Flask'])
        analyst = next(r for r in ranked if r['job_title'] == 'Data Analyst')
        self.assertEqual(analyst['percent'], 33)
        self.assertEqual(analyst['matched'], ['SQL'])
        self.assertEqual(analyst['missing'], ['Excel', 'Tableau'])

    def test_two_of_three_is_67_percent(self):
        ranked, _, _ = rank_jobs(JOBS, ['sql', 'excel'])
        self.assertEqual(ranked[0]['job_title'], 'Data Analyst')
        self.assertEqual(ranked[0]['percent'], 67)
        self.assertEqual(ranked[0]['missing'], ['Tableau'])

    def test_matching_ignores_case(self):
        ranked, _, _ = rank_jobs(JOBS, ['PYTHON', 'sql', 'fLaSk'])
        self.assertEqual(ranked[0]['percent'], 100)

    def test_results_sorted_best_first(self):
        ranked, _, _ = rank_jobs(JOBS, ['Python', 'SQL', 'Flask', 'Excel'])
        percents = [r['percent'] for r in ranked]
        self.assertEqual(percents, sorted(percents, reverse=True))

    def test_zero_matches_and_jobs_without_requirements_are_counted_not_shown(self):
        ranked, skipped, zero = rank_jobs(JOBS, ['Python'])
        titles = [r['job_title'] for r in ranked]
        self.assertNotIn('Cloud Engineer', titles)
        self.assertNotIn('No Requirements Listed', titles)
        self.assertEqual(skipped, 1)
        self.assertEqual(zero, 2)  # Data Analyst and Cloud Engineer: no required skill matched

    def test_preferred_skills_are_bonus_only(self):
        ranked, _, _ = rank_jobs(JOBS, ['SQL', 'Python'])
        analyst = next(r for r in ranked if r['job_title'] == 'Data Analyst')
        self.assertEqual(analyst['preferred_matched'], ['Python'])
        self.assertEqual(analyst['percent'], 33)  # unchanged by the preferred match

    def test_no_user_skills_gives_no_results(self):
        ranked, _, zero = rank_jobs(JOBS, [])
        self.assertEqual(ranked, [])
        self.assertEqual(zero, 3)


class CollectSkillsTests(unittest.TestCase):
    def test_distinct_and_alphabetical(self):
        self.assertEqual(collect_skills(JOBS),
                         ['AWS', 'Excel', 'Flask', 'Linux', 'Python', 'SQL', 'Tableau'])


if __name__ == '__main__':
    unittest.main()
