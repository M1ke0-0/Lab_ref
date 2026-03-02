"""
Точка входа приложения парсера hh.ru (после рефакторинга).
"""
import datetime

from hh_client import fetch_all_vacancies
from vacancy_filter import filter_vacancies
from vacancy_stats import print_statistics
from vacancy_storage import save_vacancies

SEARCH_QUERY = "python developer"
SEARCH_PAGES = 3
SEARCH_AREA = 1        # Москва
SEARCH_EXPERIENCE = "between1And3"


def build_output_filename() -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"vacancies_{timestamp}.json"


def main():
    print("Начинаем парсинг вакансий...")
    vacancies = fetch_all_vacancies(
        query=SEARCH_QUERY,
        pages=SEARCH_PAGES,
        area=SEARCH_AREA,
        experience=SEARCH_EXPERIENCE,
    )
    print(f"Получено вакансий: {len(vacancies)}")

    output_file = build_output_filename()
    save_vacancies(vacancies, output_file)
    print(f"Данные сохранены в: {output_file}")

    filtered = filter_vacancies(
        vacancies,
        min_salary=80_000,
        max_salary=300_000,
        required_skill="Python",
    )
    print(f"После фильтрации: {len(filtered)}")

    print("\n--- Статистика по всем вакансиям ---")
    print_statistics(vacancies)


if __name__ == "__main__":
    main()
