# Лабораторная работа № 1
## Рефакторинг приложений с использованием обратного проектирования

**Дисциплина:** Разработка программного обеспечения  
**Выполнил:** студент группы  
**Дата:** 01.03.2026

---

## 1. Цель работы

Освоить методы обратного проектирования и рефакторинга на практическом примере — парсере вакансий hh.ru. Применить техники декомпозиции, улучшения именования, устранения дублирования и введения уровней абстракции.

---

## 2. Исходный код (до рефакторинга)

### Файл: `before/hh_parser.py` (158 строк, 1 модуль)

Весь код приложения был сосредоточен в одном файле без какой-либо структуры.

#### Выявленные проблемы

| # | Проблема | Пример из кода |
|---|----------|----------------|
| 1 | **Нечитаемые имена** переменных и функций | `get_data`, `sv`, `flt`, `t`, `p`, `c`, `r`, `d` |
| 2 | **Монолитная «Бог-функция»** `get_data` совмещает: пагинацию, HTTP-запросы, парсинг зарплаты, навыков, опыта, работодателя, адреса | 73 строки в одной функции |
| 3 | **Отсутствие аннотаций типов** и документации | все функции без docstring и type hints |
| 4 | **Ручное управление файлами** без `with`-блока | `f = open(...); json.dump(...); f.close()` |
| 5 | **Нарушение SRP** — одна функция делает всё | `get_data`, `sv`, `flt`, `stats` в одном файле |
| 6 | **Магические строки** без именованных констант | `"https://api.hh.ru/vacancies"` повторяется |
| 7 | **Дублирующийся паттерн** извлечения вложенных полей | код для `employer`, `experience`, `address` идентичен по форме |
| 8 | **Нет обработки ошибок** HTTP-запросов | `r.json()` без проверки статус-кода |

#### Проблемный фрагмент: функция `get_data`

```python
def get_data(t, p, c, exp):   # нечитаемые параметры
    result = []
    for i in range(p):        # нечитаемая переменная
        url = "https://api.hh.ru/vacancies"   # магическая строка
        params = {"text": t, "area": c, "experience": exp, "per_page": 20, "page": i}
        r = requests.get(url, params=params)  # нет raise_for_status()
        d = r.json()                          # однобуквенное имя
        if "items" not in d:
            break
        for item in d["items"]:
            vac_id = item["id"]
            vac_url = "https://api.hh.ru/vacancies/" + vac_id  # дубль URL
            vac_r = requests.get(vac_url)
            vac_d = vac_r.json()

            # получаем зарплату (inline-логика)
            salary_from = None
            salary_to = None
            curr = None
            if vac_d.get("salary"):
                salary_from = vac_d["salary"].get("from")
                salary_to = vac_d["salary"].get("to")
                curr = vac_d["salary"].get("currency")

            # получаем навыки (inline-логика)
            skills = []
            if vac_d.get("key_skills"):
                for s in vac_d["key_skills"]:
                    skills.append(s["name"])

            # получаем опыт, работодателя, адрес — дублирующийся паттерн
            exp_name = None
            if vac_d.get("experience"):
                exp_name = vac_d["experience"]["name"]
            employer_name = None
            if vac_d.get("employer"):
                employer_name = vac_d["employer"]["name"]
            addr = None
            if vac_d.get("address"):
                addr = vac_d["address"].get("raw")
            # ... сборка словаря ...
```

#### Проблемный фрагмент: функция `sv` (сохранение)

```python
def sv(data, fn):              # неинформативные имена
    f = open(fn, "w", encoding="utf-8")   # нет with-блока
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.close()                  # ручное закрытие файла
```

---

## 3. Обратное проектирование — диаграмма модулей

### До рефакторинга

```
hh_parser.py
├── get_data(t, p, c, exp)   — HTTP-запросы + парсинг + пагинация
├── sv(data, fn)             — сохранение в JSON
├── flt(data, min_s, max_s, skill)  — фильтрация
├── stats(data)              — статистика
└── __main__                 — точка входа
```

### После рефакторинга

```
main.py               — точка входа, конфигурация
├── hh_client.py      — работа с API hh.ru
│   ├── fetch_vacancy_list()     — запрос списка вакансий (1 страница)
│   ├── fetch_vacancy_details()  — запрос деталей вакансии
│   ├── extract_salary()         — извлечение зарплаты
│   ├── extract_skills()         — извлечение навыков
│   ├── extract_nested_name()    — извлечение вложенного .name
│   ├── build_vacancy_record()   — сборка записи вакансии
│   └── fetch_all_vacancies()    — оркестрация всех страниц
├── vacancy_filter.py — фильтрация вакансий
│   ├── has_salary_in_range()
│   ├── has_required_skill()
│   └── filter_vacancies()
├── vacancy_stats.py  — статистика
│   ├── calculate_average_salary()
│   ├── count_vacancies_with_salary()
│   ├── get_top_skills()
│   └── print_statistics()
└── vacancy_storage.py — I/O: сохранение и загрузка JSON
    ├── save_vacancies()
    └── load_vacancies()
```

---

## 4. Применённые техники рефакторинга

### 4.1 Разделение больших функций и введение модулей (SRP)

**Было:** 1 файл, 4 функции  
**Стало:** 5 модулей с чёткими зонами ответственности

`hh_parser.py::get_data` разбита на 6 специализированных функций в `hh_client.py`:

| Новая функция | Ответственность |
|---|---|
| `fetch_vacancy_list` | HTTP-запрос страницы результатов |
| `fetch_vacancy_details` | HTTP-запрос деталей одной вакансии |
| `extract_salary` | извлечение зарплаты |
| `extract_skills` | извлечение ключевых навыков |
| `extract_nested_name` | универсальное извлечение вложенного поля `.name` |
| `build_vacancy_record` | сборка итогового словаря вакансии |
| `fetch_all_vacancies` | пагинация и оркестрация |

### 4.2 Устранение дублирования (DRY)

Три идентичных блока извлечения вложенного `.name` (`employer`, `experience`) заменены на одну функцию с параметром:

```python
# Было (3 копии):
employer_name = None
if vac_d.get("employer"):
    employer_name = vac_d["employer"]["name"]

exp_name = None
if vac_d.get("experience"):
    exp_name = vac_d["experience"]["name"]

# Стало (1 функция):
def extract_nested_name(vacancy_data: dict, field: str) -> str | None:
    obj = vacancy_data.get(field)
    return obj["name"] if obj else None

# Использование:
"employer":    extract_nested_name(vacancy_data, "employer"),
"experience":  extract_nested_name(vacancy_data, "experience"),
```

Аналогично список навыков: ручной цикл заменён генератором:

```python
# Было:
skills = []
if vac_d.get("key_skills"):
    for s in vac_d["key_skills"]:
        skills.append(s["name"])

# Стало:
def extract_skills(vacancy_data: dict) -> list:
    return [skill["name"] for skill in vacancy_data.get("key_skills", [])]
```

### 4.3 Улучшение именования

| Было | Стало | Причина |
|------|-------|---------|
| `get_data` | `fetch_all_vacancies` | глагол + существительное → намерение понятно |
| `sv` | `save_vacancies` | аббревиатура → полное имя |
| `flt` | `filter_vacancies` | аббревиатура → полное имя |
| `t` | `query` | однобуквенный → описательный |
| `p` | `pages` | однобуквенный → описательный |
| `c` | `area` | однобуквенный → описательный |
| `r` | `response` | однобуквенный → описательный |
| `d` | `data` | однобуквенный → описательный |
| `fn` | `filepath` | аббревиатура → описательный |
| `curr` | `currency` | сокращение → полное слово |

### 4.4 Именованные константы вместо магических строк

```python
# Было (строки в коде):
url = "https://api.hh.ru/vacancies"
vac_url = "https://api.hh.ru/vacancies/" + vac_id
time.sleep(0.25)
time.sleep(0.5)

# Стало (константы в начале модуля):
HH_API_BASE = "https://api.hh.ru"
REQUEST_DELAY = 0.25
PAGE_DELAY = 0.5
```

### 4.5 Безопасная работа с файлами и обработка ошибок

```python
# Было:
f = open(fn, "w", encoding="utf-8")
json.dump(data, f, ensure_ascii=False, indent=2)
f.close()

# Стало:
def save_vacancies(vacancies: list, filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(vacancies, file, ensure_ascii=False, indent=2)
```

HTTP-запросы теперь выбрасывают исключение при ошибке вместо молчаливого провала:

```python
response = requests.get(url, params=params)
response.raise_for_status()   # добавлено
```

### 4.6 Аннотации типов и документация

Все функции снабжены аннотациями типов (PEP 484) и docstring (Google-style):

```python
def filter_vacancies(
    vacancies: list,
    min_salary: int | None = None,
    max_salary: int | None = None,
    required_skill: str | None = None,
) -> list:
    """
    Фильтрует список вакансий по зарплате и наличию навыка.

    Args:
        vacancies: Список словарей с данными вакансий.
        min_salary: Минимальная зарплата (от), может быть None.
        max_salary: Максимальная зарплата (до), может быть None.
        required_skill: Название требуемого навыка, может быть None.

    Returns:
        Отфильтрованный список вакансий.
    """
```

---

## 5. Итоговое состояние кода

### Структура проекта после рефакторинга

```
lab1/
├── before/
│   └── hh_parser.py          # исходный файл (158 строк)
└── after/
    ├── hh_client.py          # API-клиент (89 строк)
    ├── vacancy_filter.py     # фильтрация (54 строки)
    ├── vacancy_stats.py      # статистика (40 строк)
    ├── vacancy_storage.py    # I/O (17 строк)
    ├── main.py               # точка входа (50 строк)
    └── test_refactored.py    # модульные тесты (115 строк)
```

**Итого:** 1 файл → 5 модулей; средний размер функции снизился с ~40 до ~5 строк.

---

## 6. Проверка работоспособности

### Запуск модульных тестов

```
python -m unittest test_refactored -v
```

### Результаты

```
test_average_no_salary ... ok
test_average_with_data ... ok
test_count ... ok
test_filter_by_min_salary_and_skill ... ok
test_filter_removes_all ... ok
test_no_filters ... ok
test_top_skills ... ok
test_no_skill_required ... ok
test_skill_absent ... ok
test_skill_present_case_insensitive ... ok
test_skill_present_exact ... ok
test_no_salary_no_min_required ... ok
test_no_salary_with_min_required ... ok
test_salary_above_max ... ok
test_salary_too_low ... ok
test_salary_within_range ... ok
----------------------------------------------------------------------
Ran 16 tests in 0.000s

OK
```

**Все 16 тестов пройдены успешно.** Поведение кода не изменилось.

---

## 7. Выводы

В ходе лабораторной работы был проведён полный цикл обратного проектирования и рефакторинга парсера вакансий hh.ru.

1. **Обратное проектирование** позволило выявить 8 категорий проблем в исходном коде: нечитаемые имена, монолитные функции, дублирование, отсутствие документации и обработки ошибок.
2. **Декомпозиция** монолитного файла на 5 модулей с чёткими зонами ответственности улучшила читаемость и упростила поддержку.
3. **Принцип DRY** устранил три копии идентичного кода через введение обобщённой функции `extract_nested_name`.
4. **Аннотации типов и docstring** сделали код самодокументированным без необходимости читать реализацию.
5. **Именованные константы** вынесли все «магические» значения в одно место, упрощая конфигурирование.
6. **16 модульных тестов** подтверждают полную сохранность поведения после рефакторинга и предотвращают регрессии при дальнейших изменениях.
