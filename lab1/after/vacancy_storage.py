import json


def save_vacancies(vacancies: list, filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(vacancies, file, ensure_ascii=False, indent=2)


def load_vacancies(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)
