def has_salary_in_range(vacancy: dict, min_salary: int | None, max_salary: int | None) -> bool:

    salary_from = vacancy.get("salary_from")
    salary_to = vacancy.get("salary_to")

    if min_salary is not None:
        if salary_from is None and salary_to is None:
            return False
        if salary_from is not None and salary_from < min_salary:
            return False

    if max_salary is not None:
        if salary_to is not None and salary_to > max_salary:
            return False

    return True


def has_required_skill(vacancy: dict, required_skill: str | None) -> bool:
    """Проверяет, содержит ли вакансия требуемый навык (без учёта регистра)."""
    if required_skill is None:
        return True
    return any(required_skill.lower() in skill.lower() for skill in vacancy.get("skills", []))


def filter_vacancies(
    vacancies: list,
    min_salary: int | None = None,
    max_salary: int | None = None,
    required_skill: str | None = None,
) -> list:
    return [
        vacancy for vacancy in vacancies
        if has_salary_in_range(vacancy, min_salary, max_salary)
        and has_required_skill(vacancy, required_skill)
    ]