class Employee:
    def __init__(self, name, age, zp):
        self.name = name
        self.age = age
        self.zp = zp

    @property #Инкапсуляция
    def zp(self):
        return self._zp

    @zp.setter #Инкапсуляция
    def zp(self, value):
        if not isinstance(value, (int, float)):
            raise ValueError("Введите число, а не слово!")
        if value < 0:
            raise ValueError("Зарплата не может быть отрицательной!")
        self._zp = value

class Developer(Employee):
    def __init__(self, name, age, zp, lang, projects):
        super().__init__(name, age, zp) #Наследование 
        self.lang = lang
        self.projects = projects
        
    def calculated(self):
        return self.projects * 10 #Полиморфизм - общий метод

class Manager(Employee):
    def __init__(self, name, age, zp, subord, budget):
        super().__init__(name, age, zp) #Наследование
        self.subord = subord
        self.budget = budget
        
    def calculated(self):
        return self.subord * 5 #Полиморфизм - общий метод

class Company: #Композиция - содержит в себе объекты people
    def __init__(self, title):
        self.title = title
        self.people = []
        
    def add_person(self, emp):
        self.people.append(emp)

def add_devep():
    name = input("Введите имя: ")
    age = int(input("Введите возраст: "))
    zp = float(input("Введите зарплату: "))
    lang = input("Введите язык программирования: ")
    projects = int(input("Введите количество проектов: "))
    new_dev = Developer(name, age, zp, lang, projects)
    my_company.add_person(new_dev)
    return print(f"Разработчик {name} успешно добавлен в компанию!")

def add_mang():
    name = input("Введите имя: ")
    age = int(input("Введите возраст: "))
    zp = float(input("Введите зарплату: "))
    subord = int(input("Введите количество подчинённых: "))
    budget = float(input("Введите бюджет проектов: "))
    new_mang = Manager(name, age, zp, subord, budget)
    my_company.add_person(new_mang)
    return print(f"Менеджер {name} успешно добавлен в компанию!")

def empp():
    for emp in my_company.people:
        perf = emp.calculated()
        print(f"Имя: {emp.name} | Возраст: {emp.age} | Зарплата: {emp.zp} руб. | Эффективность: {perf}")


my_company = Company("Медоёж")

while True:
    print("\n----МЕНЮ----")
    print("1. Создать сотрудника")
    print("2. Показать всех сотрудников")
    print("0. Выход")

    vibe = input()
    if vibe == "1":
        print("\nКого создать? 1 - Разработчик, 2 - Менеджер")
        who = input("Ваш выбор: ")
        
        try:
            if who == "1":
                add_devep()
            elif who =="2":
                add_mang()
        except ValueError as error:
            print(f"\n[ОШИБКА]: {error}")
            print("Сотрудник не был создан. Попробуйте ещё раз.")
            
    elif vibe =="2":
        if not my_company.people:
            print("В компании пока нет сотрудников.")
        else:
            print(f"\n Сотрудники компании: {my_company.title}")
            empp()
    elif vibe == "0":
        print("Выход из программы")
        break
    else:
        print("Неверный пункт программы!")