import requests
import json
import classes_ORM
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
    word = keywords.replace(' ', '')
    word = word.split(',')
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
        
#TODO: сделать через ORM
#функция внесения нужной информации в базу данных
def data_to_the_database():
    #присваиваем переменным значаения вакансий,городов,скиллов
    vacancy_query = classes_ORM.session.query(classes_ORM.Vacancy).all()
    city_query = classes_ORM.session.query(classes_ORM.City).all()
    skills_query = classes_ORM.session.query(classes_ORM.Skills).all()
     #формируем списки городов и вакансий
    vacancy = []
    city = []
    skills = []
    for i in vacancy_query:
        vacancy.append(i.name)
    for i in city_query:
        city.append(i.name)
    for i in skills_query:
        skills.append(i.name)
    city = set(city)
    vacancy = set(vacancy)
    skills = set(skills)
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

    #Сначала вносим данные в таблицы с вакансиями, городами и скиллами. Если такие уже есть, данные не вносятся.
    if vacancy_add not in vacancy:
        res = classes_ORM.Vacancy(vacancy_add)
        classes_ORM.session.add(res)
    else:
        print(f'вакансия {vacancy_add} уже есть')

    if city_add not in city:
        res = classes_ORM.City(city_add)
        classes_ORM.session.add(res)
    else:
        print(f'город {city_add} уже есть')

    for i in range(len(skill_name)):
        if skill_name[i] not in skills:
            res = classes_ORM.Skills(skill_name[i])
            classes_ORM.session.add(res)
        else:
            print(f'скилл {skill_name[i]} уже есть')

    #коммитим данные
    classes_ORM.session.commit()

    # Создаем session
    data = classes_ORM.session.query(classes_ORM.Data).all()
    #Вытыскмваем id добавленных или уже существующих значений города и вакансии, полученных с очередного парсинга
    id_v = classes_ORM.session.query(classes_ORM.Vacancy).filter(classes_ORM.Vacancy.name == vacancy_add).all()
    id_vacancy = []
    for i in id_v:
        id_vacancy.append(i.id)
    id_c = classes_ORM.session.query(classes_ORM.City).filter(classes_ORM.City.name == city_add).all()
    id_city = []
    for i in id_c:
        id_city.append(i.id)
    #Заливаем все данные в общую базу данных data
    for i in range(len(skill_name)):
        id_s = classes_ORM.session.query(classes_ORM.Skills).filter(classes_ORM.Skills.name == skill_name[i]).all()
        id_skill = []
        for i in id_s:
            id_skill.append(i.id)
        res_data = classes_ORM.Data(id_vacancy[0], id_city[0], vacancy_count, salary_mean, id_skill[0], skill_count[0], skill_percent[0])
        classes_ORM.session.add(res_data)
    classes_ORM.session.commit()

def look_at_my_data(vacancy, city):
    #Вытыскмваем id добавленных или уже существующих значений города и вакансии, полученных с очередного парсинга
    id_v = classes_ORM.session.query(classes_ORM.Vacancy).filter(classes_ORM.Vacancy.name == vacancy).all()
    id_vacancy = []
    for i in id_v:
        id_vacancy.append(i.id)
    id_c = classes_ORM.session.query(classes_ORM.City).filter(classes_ORM.City.name == city).all()
    id_city = []
    for i in id_c:
        id_city.append(i.id)
    # Поиск по параметрам
    res_param = classes_ORM.session.query(classes_ORM.Data).filter(classes_ORM.Data.vacancy == id_vacancy[0]).filter(classes_ORM.Data.city == id_city[0]).all()
    res = []
    for i in res_param:
        res.append(f'Вакансия: {vacancy}')
        res.append(f'Город: {city}')
        res.append(f'Средняя Зарплата: {i.salary_mean}')
        res.append(f'Количество вакансий: {i.vacancy_count}')
        break
    return res