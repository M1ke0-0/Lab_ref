import requests
import json
import time
import datetime

# парсим вакансии
def get_data(t, p, c, exp):
    result = []
    for i in range(p):
        url = "https://api.hh.ru/vacancies"
        params = {
            "text": t,
            "area": c,
            "experience": exp,
            "per_page": 20,
            "page": i
        }
        r = requests.get(url, params=params)
        d = r.json()
        if "items" not in d:
            break
        for item in d["items"]:
            vac_id = item["id"]
            vac_url = "https://api.hh.ru/vacancies/" + vac_id
            vac_r = requests.get(vac_url)
            vac_d = vac_r.json()

            # получаем зарплату
            salary_from = None
            salary_to = None
            curr = None
            if vac_d.get("salary"):
                salary_from = vac_d["salary"].get("from")
                salary_to = vac_d["salary"].get("to")
                curr = vac_d["salary"].get("currency")

            # получаем навыки
            skills = []
            if vac_d.get("key_skills"):
                for s in vac_d["key_skills"]:
                    skills.append(s["name"])

            # получаем опыт
            exp_name = None
            if vac_d.get("experience"):
                exp_name = vac_d["experience"]["name"]

            # получаем работодателя
            employer_name = None
            if vac_d.get("employer"):
                employer_name = vac_d["employer"]["name"]

            # получаем адрес
            addr = None
            if vac_d.get("address"):
                addr = vac_d["address"].get("raw")

            result.append({
                "id": vac_id,
                "name": vac_d.get("name"),
                "employer": employer_name,
                "salary_from": salary_from,
                "salary_to": salary_to,
                "currency": curr,
                "experience": exp_name,
                "skills": skills,
                "address": addr,
                "url": vac_d.get("alternate_url"),
                "published_at": vac_d.get("published_at")
            })
            time.sleep(0.25)
        time.sleep(0.5)
    return result

# сохраняем данные
def sv(data, fn):
    f = open(fn, "w", encoding="utf-8")
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.close()

# фильтруем данные
def flt(data, min_s, max_s, skill):
    r = []
    for v in data:
        ok = True
        if min_s is not None:
            if v["salary_from"] is None and v["salary_to"] is None:
                ok = False
            elif v["salary_from"] is not None and v["salary_from"] < min_s:
                ok = False
        if max_s is not None:
            if v["salary_to"] is not None and v["salary_to"] > max_s:
                ok = False
        if skill is not None:
            found = False
            for s in v["skills"]:
                if skill.lower() in s.lower():
                    found = True
                    break
            if not found:
                ok = False
        if ok:
            r.append(v)
    return r

# выводим статистику
def stats(data):
    total = len(data)
    with_salary = 0
    total_s = 0
    count_s = 0
    for v in data:
        if v["salary_from"] or v["salary_to"]:
            with_salary += 1
        if v["salary_from"]:
            total_s += v["salary_from"]
            count_s += 1
    avg = None
    if count_s > 0:
        avg = total_s / count_s

    # считаем навыки
    skill_counts = {}
    for v in data:
        for s in v["skills"]:
            if s not in skill_counts:
                skill_counts[s] = 0
            skill_counts[s] += 1

    print("Всего вакансий:", total)
    print("С зарплатой:", with_salary)
    if avg:
        print("Средняя зарплата: %.2f" % avg)
    print("Топ навыков:")
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    for sk, cnt in sorted_skills[:5]:
        print(" -", sk, ":", cnt)

# главная функция
if __name__ == "__main__":
    query = "python developer"
    pages = 3
    city = 1  # Москва
    experience = "between1And3"
    filename = "vacancies_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"

    print("Начинаем парсинг...")
    vacancies = get_data(query, pages, city, experience)
    print("Получено вакансий:", len(vacancies))

    sv(vacancies, filename)
    print("Сохранено в", filename)

    filtered = flt(vacancies, 80000, 300000, "Python")
    print("После фильтрации:", len(filtered))

    stats(vacancies)
