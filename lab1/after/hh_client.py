import requests
import time

HH_API_BASE = "https://api.hh.ru"
REQUEST_DELAY = 0.25
PAGE_DELAY = 0.5


def fetch_vacancy_list(query: str, page: int, area: int, experience: str, per_page: int = 20) -> list:
    url = f"{HH_API_BASE}/vacancies"
    params = {
        "text": query,
        "area": area,
        "experience": experience,
        "per_page": per_page,
        "page": page,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("items", [])


def fetch_vacancy_details(vacancy_id: str) -> dict:
    url = f"{HH_API_BASE}/vacancies/{vacancy_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def extract_salary(vacancy_data: dict) -> tuple:
    salary = vacancy_data.get("salary")
    if not salary:
        return None, None, None
    return salary.get("from"), salary.get("to"), salary.get("currency")


def extract_skills(vacancy_data: dict) -> list:
    return [skill["name"] for skill in vacancy_data.get("key_skills", [])]


def extract_nested_name(vacancy_data: dict, field: str) -> str | None:

    obj = vacancy_data.get(field)
    return obj["name"] if obj else None


def build_vacancy_record(vacancy_data: dict) -> dict:

    salary_from, salary_to, currency = extract_salary(vacancy_data)
    address = vacancy_data.get("address")
    return {
        "id": vacancy_data.get("id"),
        "name": vacancy_data.get("name"),
        "employer": extract_nested_name(vacancy_data, "employer"),
        "salary_from": salary_from,
        "salary_to": salary_to,
        "currency": currency,
        "experience": extract_nested_name(vacancy_data, "experience"),
        "skills": extract_skills(vacancy_data),
        "address": address.get("raw") if address else None,
        "url": vacancy_data.get("alternate_url"),
        "published_at": vacancy_data.get("published_at"),
    }


def fetch_all_vacancies(query: str, pages: int, area: int, experience: str) -> list:
    """Получает все вакансии по заданным параметрам со всех страниц."""
    vacancies = []
    for page in range(pages):
        items = fetch_vacancy_list(query, page, area, experience)
        if not items:
            break
        for item in items:
            details = fetch_vacancy_details(item["id"])
            vacancies.append(build_vacancy_record(details))
            time.sleep(REQUEST_DELAY)
        time.sleep(PAGE_DELAY)
    return vacancies
