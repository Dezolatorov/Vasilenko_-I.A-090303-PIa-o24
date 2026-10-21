from models import staff #Импортируем наш класс-шаблон сотрудника из файла models.py
from exceptions import salaryError #Импортируем исключение для недопустимой зарплаты
def add_staff(employees_list, fullname, position, department, salary): #Функция добавления нового сотрудника
    new_staff = staff(fullname, position, department, salary)
    employees_list.append(new_staff) #Закидываем созданного сотрудника в наш общий список
    print(f"Сотрудник {fullname} успешно добавлен!")

def remove_staff(employees_list, fullname): #Удаляет сотрудника по ФИО.
    for emp in employees_list: #Перебираем каждого сотрудника в списке
        if emp.fullname.lower() == fullname.lower(): #lower() нужен, чтобы поиск работал независимо от больших/маленьких букв
            employees_list.remove(emp) #Если имя совпало, то выкидываем из списка
            print(f"Сотрудник {fullname} успешно удален.")
            return
    print("Сотрудник с таким ФИО не найден.")

def change_salary(employees_list, fullname, new_salary): #Изменяет зарплату сотрудника, найденного по ФИО
    salary = float(new_salary) #Сразу проверяем, что введено число
    if salary < 0: #Отрицательная зарплата недопустима
        raise salaryError("Зарплата не может быть отрицательной")
    for emp in employees_list: #Ищем сотрудника по ФИО без учёта регистра
        if emp.fullname.lower() == fullname.lower():
            emp.salary = salary #Заменяем старое значение зарплаты новым
            print(f"Зарплата сотрудника {emp.fullname} изменена на {emp.salary} руб.")
            return True
    print("Сотрудник с таким ФИО не найден.")
    return False

def search_staff(employees_list, search_str):
    results = []
    for emp in employees_list:
        if search_str.lower() in emp.fullname.lower() or search_str.lower() in emp.department.lower(): #совпадение текста в имени или отделе
            results.append(emp) #добавляем в список результатов
    return results

def calculate_salary_stats(employees_list): #Считает статистику по зарплатам: общую, среднюю, макс и мин
    if not employees_list:
        return None # Если сотрудников нет, то и считать нечего не будет
    
    salaries = [] # Собираем все зарплаты в один список чисел
    for emp in employees_list:
        salaries.append(emp.salary)
        
    total = sum(salaries)
    avg = total / len(salaries)
    maximum = max(salaries)
    minimum = min(salaries)
    
    return {
        "total": total,
        "average": avg,
        "max": maximum,
        "min": minimum
    }