class Person: #базовый класс - человек
    def __init__(self, name): #конструктор класса, вызывается при создании объекта
        self.name = name #сохраняем имя в атрибут объекта

    def __str__(self):
        return f"{self.name}"


class Employee(Person): #производный класс - сотрудник(работник)
    def __init__(self, name, department, position, salary):
        super().__init__(name)
        self.department = department
        self.position = position
        self.salary = salary

    def __str__(self):
        return (f"{self.name} | Отдел: {self.department} | "
                f"Должность: {self.position} | Зарплата: {self.salary}")


class Manager(Employee): #производный класс руководитель
    def __init__(self, name, department, position, salary, bonus): #записывает значения в атриьбуты объекта
        super().__init__(name, department, position, salary)
        self.bonus = bonus

    def __str__(self): #красивый вывод на экран(красивый и понятный текстовый вид объекта.)
        return (f"{self.name} | Отдел: {self.department} | "
                f"Должность: {self.position} | Зарплата: {self.salary} | "
                f"Бонус: {self.bonus}")