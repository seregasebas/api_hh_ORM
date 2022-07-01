import requests
import json
import sqlite3

#функция получения словаря id - name города
def id_name(city):
    goroda = requests.get('https://api.hh.ru/areas/').json()
    city = city.lower()
    id_name = {}
    for i in range(len(goroda)):
        for e in range(len(goroda[i]['areas'])):
            id_name[goroda[i]['areas'][e]['name'].lower()] = goroda[i]['areas'][e]['id']
    
    return id_name[city]


#функция получения с сайта данных
def api_hh(vacancy, city):

    url = 'https://api.hh.ru/vacancies'

    params = {
        'text': f'NAME:({vacancy})', #вакансия
        'area': city,                #Город
    }

    #Записываем количество страниц с найденной инфой
    pages = requests.get(url, params=params).json()['pages']
    num = requests.get(url, params=params).json()['per_page']
    #количество вакансий
    found_vacations = requests.get(url, params=params).json()['found']
    
    print(f'количество страниц: {pages}')
    print(f'количество tiks на странице: {num}')
    #Переберем все страницы с нужными нам параметрами и запишем в список
    res_all = []
    for page in range(pages):
        print(f'страница номер: {page+1}')
        params = {
            'text': f'NAME:({vacancy})', #вакансия
            'area': city,                #Город
            }
        res_all.append(requests.get(url, params=params).json())
    
    return res_all, found_vacations

def salary_mean(res_all):
    #Достаем зарплаты - оба числа от и до
    res = []
    for i in range(len(res_all)):
        for e in range(len(res_all[i]['items'])):
            if res_all[i]['items'][e]['salary'] != None:
                res.append(res_all[i]['items'][e]['salary']['from'])
                res.append(res_all[i]['items'][e]['salary']['to'])
    #Убираем None
    res_sum = []
    for salary in res:
        if salary != None:
            res_sum.append(salary)
    #Вычисляем среднюю
    res_mean = sum(res_sum)/len(res_sum) 
    return f'{round((res_mean), 0)}'

#Достанем все требования к вакансиям
def requirements(res_all):
    requirement = []
    for i in range(len(res_all)):
        for e in range(len(res_all[i]['items'])):
            requirement.append(res_all[i]['items'][e]['snippet']['requirement'])
    return requirement

def requirement_count(requirement, keywords):
    word = keywords.split(',')
    total = 0
    dict_word = {}
    for i in word:
        for req in range(len(requirement)):
            if requirement[req] != None:
                if i.lower() in requirement[req].lower():
                    total += 1
        dict_word[i] = total
    dict_word_sorted = sorted(dict_word.items(), key = lambda x: x[1], reverse = True)

    #количество вакасний по ключевым словам
    count_key_words = 1
    for i in range(len(dict_word_sorted)):
        count_key_words += dict_word_sorted[i][1]

    #словарь с вакансиями и проыентами по ключевым словам
    dict_word_new = {'requirement_count':[{} for i in range(len(dict_word_sorted))]}
    for i in range(len(dict_word_new['requirement_count'])):
        dict_word_new['requirement_count'][i]['name'] = dict_word_sorted[i][0]
        dict_word_new['requirement_count'][i]['count'] = dict_word_sorted[i][1]
        dict_word_new['requirement_count'][i]['percent'] = f'{round((dict_word_sorted[i][1]/count_key_words)*100, 2)}%'

    return dict_word_new, count_key_words

#Функция объединения данных в словарь для создания файла json
def merged_dict(vacancy, city, keywords, requirement_count, vacancy_count, salary_mean, count_key_words):
    new_dict = {}
    new_dict['vacancy'] = vacancy
    new_dict['city'] = city
    new_dict['keywords'] = keywords
    new_dict['vacancy_count'] = vacancy_count
    new_dict['count_key_words'] = count_key_words
    new_dict['salary_mean'] = salary_mean
    new_dict['requirement_count'] = requirement_count['requirement_count']
    return new_dict

#функция сохранения json файла
def save_file(new_dict):
    with open("api_hh.json", "w", encoding='utf-8') as write_file:
        json.dump(new_dict, write_file)

#функция внесения нужной информации в базу данных
def data_to_the_database():
    # Подключение к базе данных
    conn = sqlite3.connect('hh_api_data.db')   
    # Создаем курсор
    cursor = conn.cursor()
    #присваиваем переменным значаения вакансий,городов,скиллов
    cursor.execute('SELECT * from vacancy')
    vacancy = cursor.fetchall()
    cursor.execute('SELECT * from city')
    city = cursor.fetchall()
    cursor.execute('SELECT * from skills')
    skills = cursor.fetchall()
    #формируем списки городов и вакансий
    city_all = []
    vacancy_all = []
    skills_all = []
    for i in city:
        city_all.append(i[1])
    for i in vacancy:
        vacancy_all.append(i[1])
    for i in skills:
        skills_all.append(i[1])
    city_all = set(city_all)
    vacancy_all = set(vacancy_all)
    skills_all = set(skills_all)
    #открываем json файл с данными парсинга
    with open('api_hh.json', 'r', encoding='utf-8') as f: #открыли файл с данными
        text = json.load(f) #загнали все, что получилось в переменную
    #присваиваем значения к нужным переменным
    city_add = text['city']
    vacancy_add = text['vacancy']
    vacancy_count = text['vacancy_count']
    salary_mean = text['salary_mean']
    #Также делаем списки из навыков
    requirement_count = text['requirement_count']
    skill_name, skill_count, skill_percent = [],[],[]
    for i in range(len(requirement_count)):
        skill_name.append(text['requirement_count'][i]['name'])
        skill_count.append(text['requirement_count'][i]['count'])
        skill_percent.append(text['requirement_count'][i]['percent'])

    #Сначала вносим данные в таблицы с вакансиями и городами. Если такие уже есть, данные не вносятся.
    if vacancy_add not in vacancy_all:
        cursor.execute("insert into vacancy(name) VALUES (?)", (vacancy_add,))
    else:
        print(f'вакансия {vacancy_add} уже есть')

    if city_add not in city_all:
        cursor.execute("insert into city(name) VALUES (?)", (city_add,))
    else:
        print(f'город {city_add} уже есть')

    for i in range(len(skill_name)):
        if skill_name[i] not in skills_all:
            cursor.execute("insert into skills(name) VALUES (?)", (skill_name[i],))
        else:
            print(f'скилл {skill_name[i]} уже есть')

    #коммитим данные
    conn.commit()
    # Создаем курсор
    cursor = conn.cursor()
    #Вытыскмваем id добавленных или уже существующих значений города и вакансии, полученных с очередного парсинга
    cursor.execute("SELECT ID FROM vacancy WHERE name LIKE (?)", (vacancy_add,))
    id_vacancy = cursor.fetchall()
    cursor.execute("SELECT ID FROM city WHERE name LIKE (?)", (city_add,))
    id_city = cursor.fetchall()
    #Заливаем все данные в общую базу данных data
    for i in range(len(skill_name)):
        cursor.execute("SELECT ID FROM skills WHERE name LIKE (?)", (skill_name[i],))
        id_skill = cursor.fetchall()
        cursor.execute("INSERT into data(vacancy,city,vacancy_count,salary_mean,skill_name, skill_count, skill_percent) values(?,?,?,?,?,?,?)", (id_vacancy[0][0], id_city[0][0], vacancy_count, salary_mean, id_skill[0][0], skill_count[i], skill_percent[i]))
    #Сораняем и закрываем изменения в базе данных
    conn.commit()
    conn.close()

def look_at_my_data(vacancy, city):
    # Подключение к базе данных
    conn = sqlite3.connect('hh_api_data.db')
    # Создаем курсор
    cursor = conn.cursor()
    #Задаем параметры для вывода
    cursor.execute("SELECT d.id, v.name, c.name, d.salary_mean, d.vacancy_count, s.name, d.skill_count, d.skill_percent  from data d, vacancy v, city c, skills s where d.vacancy = v.id and d.city = c.id and d.skill_name = s.id")
    data = cursor.fetchall()
    res = []
    for i in range(len(data)):
        if vacancy in data[i] and city in data[i]:
            res.append(data[i])
    return res