"""
Модуль статистики по вакансиям.
"""
from collections import Counter


def calculate_average_salary(vacancies: list) -> float | None:
    """Вычисляет среднюю зарплату (от) по вакансиям, у которых она указана."""
    salaries = [v["salary_from"] for v in vacancies if v.get("salary_from") is not None]
    if not salaries:
        return None
    return sum(salaries) / len(salaries)


def count_vacancies_with_salary(vacancies: list) -> int:
    """Подсчитывает количество вакансий с указанной зарплатой."""
    return sum(1 for v in vacancies if v.get("salary_from") or v.get("salary_to"))


def get_top_skills(vacancies: list, top_n: int = 5) -> list[tuple]:
    """Возвращает топ-N самых популярных навыков среди вакансий."""
    all_skills = [skill for v in vacancies for skill in v.get("skills", [])]
    return Counter(all_skills).most_common(top_n)


def print_statistics(vacancies: list) -> None:
    """Выводит сводную статистику по списку вакансий."""
    total = len(vacancies)
    with_salary = count_vacancies_with_salary(vacancies)
    avg_salary = calculate_average_salary(vacancies)
    top_skills = get_top_skills(vacancies)

    print(f"Всего вакансий: {total}")
    print(f"С указанной зарплатой: {with_salary}")
    if avg_salary is not None:
        print(f"Средняя зарплата (от): {avg_salary:,.2f}")
    print("Топ навыков:")
    for skill, count in top_skills:
        print(f"  - {skill}: {count}")
