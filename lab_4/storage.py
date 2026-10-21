import json #для работы с форматом данных JSON
import csv  #для работы с табличным форматом CSV
from models import staff

JSON_FILE = "employees.json"  #Создаем переменную с именем файла для сохранения базы данных
CSV_FILE = "employees.csv"

def save_to_json(employees_list): #Перебираем всех сотрудников и превращаем их в словари
    staff_list = []
    for emp in employees_list:
        staff_list.append(emp.to_dict())  #Превращаем сотрудника в словарь и добавляем в наш список
    with open(JSON_FILE, "w", encoding="utf-8") as f: #Открываем JSON-файл для записи в понятной кодировке UTF-8
        json.dump(staff_list, f, ensure_ascii=False, indent=4) # Записываем даные в файле f

def load_from_json(): #Создаем функцию, которая читает людей из файла при старте программы
    try: #Проверяет есть ли файл на диске
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            dicts_list = json.load(f)
            
            employees_list = [] # Список для сбора сотрудников
            for d in dicts_list:
                employees_list.append(staff.from_dict(d)) #Превращаем плоский словарь обратно в класс staff
                
            return employees_list
    except (FileNotFoundError, json.JSONDecodeError):
        return [] # Если файла нет, возвращаем пустой список, чтобы программа не падала

def export_to_csv(employees_list): #Создаем функцию для выгрузки базы в красивую таблицу CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f: #"" Чтобы не было пустых строк
        writer = csv.writer(f) #Создаем специального робота-писателя, который умеет делать строки таблицы
        writer.writerow(["ФИО", "Должность", "Отдел", "Зарплата"]) # Записываем шапку таблицы
        
        for emp in employees_list: # Записываем данные каждого сотрудника
            writer.writerow([emp.fullname, emp.position, emp.department, emp.salary]) #Пишем в строчку в таблице