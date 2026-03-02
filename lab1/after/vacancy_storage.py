"""
Модуль сохранения/загрузки данных о вакансиях.
"""
import json


def save_vacancies(vacancies: list, filepath: str) -> None:
    """Сохраняет список вакансий в JSON-файл в кодировке UTF-8."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(vacancies, file, ensure_ascii=False, indent=2)


def load_vacancies(filepath: str) -> list:
    """Загружает список вакансий из JSON-файла."""
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)
