staff = [
    {"фио": "Иванов Иван Иванович", "должность": "Программист", "отдел": "IT", "зарплата": 120000},
    {"фио": "Петров Петр Петрович", "должность": "Тестировщик", "отдел": "IT", "зарплата": 80000},
    {"фио": "Сидорова Анна Сергеевна", "должность": "Бухгалтер", "отдел": "Бухгалтерия", "зарплата": 95000},
    {"фио": "Кузнецов Олег Игоревич", "должность": "Программист", "отдел": "IT", "зарплата": 150000},
    {"фио": "Смирнова Елена Викторовна", "должность": "HR-менеджер", "отдел": "Кадры", "зарплата": 70000}
]

def add_worker(spisok): # Добавление нового сотрудника с защитой от ввода букв
    fio = input("Введите ФИО: ")
    pos = input("Введите должность: ")
    dept = input("Введите отдел: ")
    
    try:
        sal = int(input("Введите зарплату (числом): "))
        new_worker = {"фио": fio, "должность": pos, "отдел": dept, "зарплата": sal}
        spisok.append(new_worker)
        print("Сотрудник успешно добавлен!")
    except ValueError:
        print("Ошибка: Зарплата должна быть числом! Сотрудник не добавлен.")

def unique_positions(spisok): # Уникальность должностей 
    position = set() # Хранение в неупорядоченном виде/ убрать дубликаты
    for i in spisok:
        position.add(i['должность'])
    print("Уникальные должности:", position)

def show_all(spisok): # Показать всех сотрудников 
    for worker in spisok:
        print(f"{worker['фио']} | {worker['должность']} | {worker['отдел']} | {worker['зарплата']} руб.")

def samiy_cool(spisok): # Самый высокооплачиваемый сотрудник 
    max_staff = spisok[0]
    for i in spisok:
        if i['зарплата'] > max_staff['зарплата']:
            max_staff = i
    print(f"Самый высокооплачиваемый: {max_staff['фио']} ({max_staff['зарплата']} руб.)")

def sr_zp(spisok): # Рассчёт средней з/п
    total = 0
    for worker in spisok:
        total = total + worker['зарплата']

    a_total = total / len(spisok)
    print(f"Средная зарплата: {a_total}")

def sort_zp(spisok): # Сортировка по зп
    sorted_staff = sorted(spisok, key=lambda x: x['зарплата'])
    for i in sorted_staff:
        print(f"{i['фио']}: {i['зарплата']} руб.")

def poisk_it(spisok): # Поиск сотрудника по отделу и вывод его aамилии
    otd = input("Введите отдел: ")
    naideno = False
    for worker in spisok:
        if worker['отдел'] == otd:
            print(f"{worker['фио']} | {worker['должность']} | {worker['отдел']} | {worker['зарплата']} руб.")
            naideno = True     
    if naideno == False:
        print('Такого отдела нет или в нём нет сотрудников.')

def filtr_zp(spisok): # Фильтрация по зарплате
    try:
        porog = int(input("Показать сотрудников с зарплатой больше или равной: "))
        naideno = False
        for worker in spisok:
            if worker['зарплата'] >= porog:
                print(f"{worker['фио']} | {worker['должность']} | {worker['отдел']} | {worker['зарплата']} руб.")
                naideno = True
        if naideno == False:
            print("Нет сотрудников с такой высокой зарплатой.")
    except ValueError:
        print("Ошибка: Нужно ввести число.")

while True: # Главное меню программы
    print("\n===== МЕНЮ =====")
    print("1. Посчитать среднюю зарплату")
    print("2. Поиск сотрудников по отделу")
    print("3. Добавить нового сотрудника")
    print("4. Все сотрудники")
    print("5. Самый высокооплачиваемый сотрудник")
    print("6. Уникальность должностей")
    print("7. Сортировка по зп")
    print("8. Фильтрация по зарплате")
    print("0. Выход")
    
    vibor = input("Выбери пункт: ") 
    
    if vibor == "1":
        sr_zp(staff)
    elif vibor == "2":
        poisk_it(staff)
    elif vibor == "3":
        add_worker(staff)
    elif vibor == "4":
        show_all(staff)
    elif vibor == "5":
        samiy_cool(staff)
    elif vibor == "6":
        unique_positions(staff)
    elif vibor == "7":
        sort_zp(staff)
    elif vibor == "8":
        filtr_zp(staff)
    elif vibor == "0":
        print("Выход из программы")
        break
    else:
        print("Неверный пункт меню!")