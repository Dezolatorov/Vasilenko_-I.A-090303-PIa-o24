from functools import reduce #инструменты для работы с функциями в функциональном стиле(элементы коллекции в одно значение)

def filter_objects(objects, predicate): #подходит элемент под условие или нет (фильтрация по предикату наших сотрудников)
    return filter(predicate, objects)


def transform_objects(objects, operation): #преобразование объектов (что нам делать с каждым элементом)
    return map(operation, objects) #возвращает итератор, в котором к каждому элементу objects применена функция operation


def sort_objects(objects, key_function): #функция, которая для каждого элемента возвращает значение, по которому сравнивать
    return sorted(objects, key=key_function)


def find_max_salary(objects):
    if not objects:
        return None
    return max(objects, key=lambda emp: emp.salary)


def has_department(objects, department):  #проверяет, есть ли хотя бы один сотрудник в указанном отделе
    return any(emp.department == department for emp in objects)


def all_salaries_positive(objects):     #проверяет, что все зарплаты > 0
    return all(emp.salary > 0 for emp in objects) #перебираем каждого сотрудника и проверяем положительная ли зарплата.


def get_positions(objects): #возвращает список должностей (через map)
    return list(map(lambda emp: emp.position, objects)) #применяем проверку операции(берём сотрудника и возвращаем его должность)


def total_salary(objects):
    if not objects:
        return 0
    return reduce(lambda acc, emp: acc + emp.salary, objects, 0) #берём накопленное значение и складываем его поочерёдно в стекущим значением


def make_salary_filter(min_salary): #замыкание: фабрика предикатов, запоминающая порог зарплаты
    def predicate(employee): #вложенная функция видит min_salary из внешней области видимости
        return employee.salary > min_salary
    return predicate #возвращаем функцию, а не результат — порог «запоминается» в замыкании


def make_department_filter(department): #замыкание: предикат по отделу, без учёта регистра
    normalized = department.strip().lower() #нормализуем один раз, до создания предиката

    def predicate(employee):
        return employee.department.strip().lower() == normalized
    return predicate