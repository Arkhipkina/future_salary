from terminaltables import AsciiTable
import os
import requests
from itertools import count
from dotenv import load_dotenv

PROGRAMMER_SPECIALIZATION = "1.221"
MOSCOW_ID = "1"
DAYS_IN_PERIOD = 30
PROGRAMMING_CATALOGUE = 48
HH_TITLE = "HeadHunter Moscow"
SJ_TITLE = "SuperJob Moscow"

def predict_rub_salary(salary_from=None, salary_to=None):
    average_salary = None
    if salary_from and salary_to:
        average_salary = (salary_to + salary_from) / 2
    elif salary_from:
        average_salary = salary_from * 1.2
    elif salary_to:
        average_salary = salary_to * 0.8
    return average_salary


def get_vacancies_hh(language, page=0):
    url = "https://api.hh.ru/vacancies"

    params = {
        "specialization": PROGRAMMER_SPECIALIZATION,
        "text": language,
        "area": MOSCOW_ID,
        "period": DAYS_IN_PERIOD,
        "page": page,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def get_intelligence_vacancies_hh(language):
    average_salaries = []
    counter = 0

    for page in count(0,1):
        response = get_vacancies_hh(language, page=page)

        for vacancy in response["items"]:
            if vacancy["salary"] and vacancy["salary"]["currency"] == "RUR":
                average_salaries.append(predict_rub_salary(vacancy["salary"]["from"], vacancy["salary"]["to"]))
                counter += 1

        if page >= response["pages"] - 1:
            break

    vacancies_found = response["found"]
    if len(average_salaries) == 0:
        average_salary = 0
    elif len(average_salaries) > 0:
        average_salary = sum(average_salaries) / len(average_salaries)

    intelligence_vacancies = {
        "vacancies_found": vacancies_found,
        "vacancies_processed": counter,
        "average_salary": average_salary
    }

    return intelligence_vacancies


def get_statistics_language_hh(languages):
    vacancies_languages = {}
    for language in languages:
        vacancies_languages[language] = get_intelligence_vacancies_hh(language)
    return vacancies_languages


def get_vacancies_sj(key, language, page=0):
    url = "https://api.superjob.ru/2.0/vacancies/"

    headers = {
        "X-Api-App-Id": key
    }
    params = {
        "town": "Moscow",
        "period": DAYS_IN_PERIOD,
        "keyword": language,
        "catalogues": PROGRAMMING_CATALOGUE,
        "page": page
    }
        
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()

    return response.json()


def get_intelligence_vacancies_sj(language, key):
    average_salaries = []
    counter = 0
    for page in count(0, 1):
        response = get_vacancies_sj(key, language, page=page)

        for vacancy in response["objects"]:
            if vacancy["payment_from"] or vacancy["payment_to"]:
                if vacancy["currency"] == "rub":
                    average_salaries.append(predict_rub_salary(vacancy["payment_from"], vacancy["payment_to"]))
                    counter += 1

        if not response["more"]:
            break

    vacancy_count = response["total"]
    if len(average_salaries) == 0:
        average_salary = 0
    elif len(average_salaries) > 0:
        average_salary = sum(average_salaries) / len(average_salaries)

    vacancies_for_language = {
        "vacancies_found": vacancy_count,
        "vacancies_processed": counter,
        "average_salary": int(average_salary)
    }
    return vacancies_for_language


def get_statistics_language_sj(languages, key):
    vacancies_languages = {}
    for language in languages:
        vacancies_languages[language] = get_intelligence_vacancies_sj(language, key)
    return vacancies_languages


def create_table(title, statistics):
    table_data = [
        ["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]
    ]
    for language, vacancies in statistics.items():
        table_data.append([language, vacancies["vacancies_found"], vacancies["vacancies_processed"], vacancies["average_salary"]])
    table = AsciiTable(table_data, title)
    return table.table


def main():
    load_dotenv()

    sj_secret_key = os.environ['SUPERJOB_SECRET_KEY']
    
    languages = [
        "JavaScript", "Java", "Python", "PHP", "C++", "CSS", "C#", "C",
        "Go"
    ]
    

    hh_table = create_table(HH_TITLE, get_statistics_language_hh(languages))
    sj_table = create_table(SJ_TITLE, get_statistics_language_sj(languages, sj_secret_key))
    print(f"{sj_table}\n{hh_table}")
    


if __name__ == "__main__":
    main()