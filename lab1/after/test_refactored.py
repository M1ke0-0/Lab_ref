"""
Тесты для модулей после рефакторинга.
"""
import unittest
from vacancy_filter import has_salary_in_range, has_required_skill, filter_vacancies
from vacancy_stats import calculate_average_salary, count_vacancies_with_salary, get_top_skills


# ---------- Фикстуры ----------

VACANCY_WITH_SALARY = {
    "id": "1",
    "name": "Python Developer",
    "salary_from": 100_000,
    "salary_to": 200_000,
    "currency": "RUR",
    "skills": ["Python", "Django", "PostgreSQL"],
}

VACANCY_NO_SALARY = {
    "id": "2",
    "name": "Junior Dev",
    "salary_from": None,
    "salary_to": None,
    "currency": None,
    "skills": ["JavaScript", "React"],
}

VACANCY_LOW_SALARY = {
    "id": "3",
    "name": "Intern",
    "salary_from": 30_000,
    "salary_to": 50_000,
    "currency": "RUR",
    "skills": ["Python"],
}

ALL_VACANCIES = [VACANCY_WITH_SALARY, VACANCY_NO_SALARY, VACANCY_LOW_SALARY]


# ---------- Тесты фильтрации ----------

class TestHasSalaryInRange(unittest.TestCase):
    def test_salary_within_range(self):
        self.assertTrue(has_salary_in_range(VACANCY_WITH_SALARY, 80_000, 300_000))

    def test_salary_too_low(self):
        self.assertFalse(has_salary_in_range(VACANCY_LOW_SALARY, 80_000, 300_000))

    def test_no_salary_with_min_required(self):
        self.assertFalse(has_salary_in_range(VACANCY_NO_SALARY, 50_000, None))

    def test_no_salary_no_min_required(self):
        self.assertTrue(has_salary_in_range(VACANCY_NO_SALARY, None, None))

    def test_salary_above_max(self):
        self.assertFalse(has_salary_in_range(VACANCY_WITH_SALARY, None, 150_000))


class TestHasRequiredSkill(unittest.TestCase):
    def test_skill_present_exact(self):
        self.assertTrue(has_required_skill(VACANCY_WITH_SALARY, "Python"))

    def test_skill_present_case_insensitive(self):
        self.assertTrue(has_required_skill(VACANCY_WITH_SALARY, "python"))

    def test_skill_absent(self):
        self.assertFalse(has_required_skill(VACANCY_WITH_SALARY, "Java"))

    def test_no_skill_required(self):
        self.assertTrue(has_required_skill(VACANCY_WITH_SALARY, None))


class TestFilterVacancies(unittest.TestCase):
    def test_filter_by_min_salary_and_skill(self):
        result = filter_vacancies(ALL_VACANCIES, min_salary=80_000, required_skill="Python")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "1")

    def test_no_filters(self):
        result = filter_vacancies(ALL_VACANCIES)
        self.assertEqual(len(result), 3)

    def test_filter_removes_all(self):
        result = filter_vacancies(ALL_VACANCIES, min_salary=500_000)
        self.assertEqual(len(result), 0)


# ---------- Тесты статистики ----------

class TestCalculateAverageSalary(unittest.TestCase):
    def test_average_with_data(self):
        avg = calculate_average_salary(ALL_VACANCIES)
        self.assertAlmostEqual(avg, 65_000.0)

    def test_average_no_salary(self):
        avg = calculate_average_salary([VACANCY_NO_SALARY])
        self.assertIsNone(avg)


class TestCountVacanciesWithSalary(unittest.TestCase):
    def test_count(self):
        self.assertEqual(count_vacancies_with_salary(ALL_VACANCIES), 2)


class TestGetTopSkills(unittest.TestCase):
    def test_top_skills(self):
        top = get_top_skills(ALL_VACANCIES, top_n=1)
        self.assertEqual(top[0][0], "Python")
        self.assertEqual(top[0][1], 2)


if __name__ == "__main__":
    unittest.main()
