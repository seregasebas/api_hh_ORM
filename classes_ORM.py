from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3

engine = create_engine('sqlite:///hh_api_data.db', echo=True)
Base = declarative_base()
# Создание сессии
Session = sessionmaker(bind=engine)
# create a Session
session = Session()

class Data(Base):
    __tablename__ = 'data'
    id = Column(Integer, primary_key=True)
    vacancy = Column(String, ForeignKey('vacancy.id'))
    city = Column(String, ForeignKey('city.id'))
    vacancy_count = Column(Integer, nullable=True)
    salary_mean = Column(Integer, nullable = True)
    skill_name = Column(String, ForeignKey('skills.id'))
    skill_count = Column(Integer, nullable = True)
    skill_percent = Column(Integer, nullable = True)

    def __init__(self, vacancy, city, vacancy_count, salary_mean, skill_name, skill_count, skill_percent):
        self.vacancy = vacancy
        self.city = city
        self.vacancy_count = vacancy_count
        self.salary_mean = salary_mean
        self.skill_name = skill_name
        self.skill_count = skill_count
        self.skill_percent= skill_percent

    def __str__(self):
        return f'{self.id}, {self.vacancy} - средняя зарплата = {self.salary_mean}, {self.city}'

class Vacancy(Base):
    __tablename__ = 'vacancy'
    id = Column(Integer, primary_key = True)
    name = Column(String)

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'name vacation is {self.name}'

class City(Base):
    __tablename__ = 'city'
    id = Column(Integer, primary_key = True)
    name = Column(String)

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'city is {self.name}'

class Skills(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key = True)
    name = Column(String)

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'skil_name is {self.name}'
