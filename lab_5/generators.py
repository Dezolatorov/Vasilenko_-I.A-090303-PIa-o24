def employee_generator(objects, department): # генератор: выдаёт сотрудников выбранного отдела по одному
    for emp in objects:
        if emp.department == department:
            yield emp #запоминает своё состояние и может выдавать значения по одному


class EmployeeIterator: #итератор для перебора сотрудников
    def __init__(self, objects):
        self.objects = objects #сохраняем коллекцию внутрь объекта
        self.index = 0 #начинаем с первого элемента

    def __iter__(self): #возвращаем сам итератор
        return self

    def __next__(self): #возвращает следующий элемент или поднимает StopIteration
        if self.index >= len(self.objects):
            raise StopIteration
        result = self.objects[self.index]
        self.index += 1
        return result