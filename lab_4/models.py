from exceptions import salaryError # Импортируем нашу личную ошибку из файла exceptions.py

class staff: #Описание сотрудника
    def __init__(self, fullname, position, department, salary):
        if float(salary) < 0:
            raise salaryError("Зарплата не может быть отрицательной")
        self.fullname = fullname #Записываем данные и привязываем к ключам
        self.position = position
        self.department = department
        self.salary = float(salary)
        
    def to_dict(self): # Метод, который превращает сотрудника в словарь JSON
        return{ #Возвращаем и привязываем значения к ключам
            "fullname": self.fullname,
            "position": self.position,
            "department": self.department,
            "salary": self.salary
        }

    @classmethod # Метка, что метод работает со всем классом, а не с конкретным объектом
    def from_dict(cls, data):# Метод, который создает сотрудника заново из готового словаря data
        return cls(
            fullname=data["fullname"], # Передаём данные из словаря
            position=data["position"],
            department=data["department"],
            salary=data["salary"]
        )
    def __str__(self): # Перевёл в обычный текст без мусора
         return f"{self.fullname} | {self.position} | Отдел: {self.department} | Зарплата: {self.salary} руб."