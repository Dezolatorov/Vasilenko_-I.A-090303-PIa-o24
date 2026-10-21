from typing import List, Any  # Подключаем типы списков и произвольных данных для аннотаций
import inspect  # Подключаем встроенный модуль для глубокого анализа структуры объектов
from datetime import date, timedelta  # Подключаем работу с текущими датами и интервалами дней
from models import LibraryEdition, LibraryStatus, Book, Magazine, DigitalEdition  # Импортируем классы моделей и перечисление статусов
from exceptions import EntityNotFoundError, InvalidStateError  # Импортируем кастомные классы ошибок для бизнес-логики
from decorators import log_call, measure_time, limit_calls  # Импортируем три разработанных декоратора по ТЗ
from protocols import Reportable  # Импортируем интерфейс-протокол для генерации отчетов

class LibraryService:  # Главный сервисный класс бизнес-логики управления библиотечным фондом
    """Класс бизнес-логики управления библиотечным фондом."""
    def __init__(self) -> None:  # Конструктор: инициализирует объект сервиса при создании
        self.editions: List[LibraryEdition] = []  # Список-коллекция для хранения всех изданий в памяти

    @log_call  # Геттер-декоратор: логирует вызов, входные аргументы и результат метода
    def add_edition(self, edition: LibraryEdition) -> None:  # Метод добавления нового объекта (книги/журнала/файла) в фонд
        self.editions.append(edition)  # Добавляем полученное издание в конец списка фонда

    @log_call  # Геттер-декоратор: автоматически записывает в терминал факт удаления объекта
    def delete_edition(self, edition_id: int) -> None:  # Метод удаления любого библиотечного издания из фонда по ID
        edition = self.find_by_id(edition_id)  # Ищем объект по его уникальному номеру через встроенный метод
        self.editions.remove(edition)  # Стираем найденное издание из общей коллекции нашего фонда

    @measure_time  # Декоратор замера времени: выведет скорость выполнения поиска в консоль
    def find_by_id(self, edition_id: int) -> LibraryEdition:  # Метод поиска конкретного издания по его числовому ID
        for ed in self.editions:  # Запускаем цикл перебора всех элементов коллекции по очереди
            if ed.id == edition_id:  # Если идентификатор текущей книги совпал с искомым
                return ed  # Возвращаем найденный объект и мгновенно выходим из метода
        raise EntityNotFoundError(f"Издание с ID {edition_id} не найдено в фонде.")  # Если цикл завершен — кидаем ошибку

    @log_call  # Журналирует параметры проведенной операции выдачи книги читателю
    @measure_time  # Фиксирует точное время процессора, затраченное на метод выдачи
    def issue_edition(self, edition_id: int, days_to_borrow: int = 14) -> str:  # Доп. операция 1: выдача издания на руки
        edition = self.find_by_id(edition_id)  # Находим нужную книгу по ID. Если её нет — сработает ошибка выше
        if edition.status not in (LibraryStatus.AVAILABLE, LibraryStatus.RESERVED):  # Выдать можно только свободную или забронированную книгу
            raise InvalidStateError(f"Невозможно выдать. Текущий статус издания: '{edition.status.value}'.")  # Запрещаем выдачу
        
        edition.status = LibraryStatus.ISSUED  # Меняем текущий статус найденного издания на "выдано"
        edition.due_date = date.today() + timedelta(days=days_to_borrow)  # Рассчитываем дедлайн возврата: сегодня + N дней
        return f"Издание '{edition.title}' выдано читателю. Срок возврата: {edition.due_date}"  # Возвращаем итог операции

    @log_call  # Автоматически запишет лог об успешном или неуспешном возврате издания
    def return_edition(self, edition_id: int) -> str:  # Доп. операция 2: возврат выданной книги обратно на полку
        edition = self.find_by_id(edition_id)  # Ищем сдаваемую книгу по её уникальному идентификатору
        if edition.status != LibraryStatus.ISSUED:  # Проверяем: если книгу никто не брал и она уже на полке
            raise InvalidStateError(f"Издание не находится в статусе 'выдано'. Текущий статус: '{edition.status.value}'.")  # Ошибка логики
        
        edition.status = LibraryStatus.AVAILABLE  # Сбрасываем статус издания обратно на базовый "доступно"
        edition.due_date = None  # Очищаем дату возврата, так как задолженность перед фондом закрыта
        return f"Издание '{edition.title}' успешно возвращено в фонд."  # Возвращаем текстовый отчет об успехе

    @log_call  # Журналирует факт бронирования издания
    def reserve_edition(self, edition_id: int, days_to_hold: int = 3) -> str:  # Доп. операция: бронирование издания
        edition = self.find_by_id(edition_id)  # Ищем издание по ID
        if edition.status != LibraryStatus.AVAILABLE:  # Забронировать можно только свободное издание
            raise InvalidStateError(f"Невозможно забронировать. Текущий статус: '{edition.status.value}'.")
        edition.status = LibraryStatus.RESERVED  # Переводим издание в статус "зарезервировано"
        edition.due_date = date.today() + timedelta(days=days_to_hold)  # Срок, до которого держим бронь
        return f"Издание '{edition.title}' зарезервировано до {edition.due_date}."

    @log_call  # Журналирует снятие брони
    def cancel_reservation(self, edition_id: int) -> str:  # Отмена бронирования
        edition = self.find_by_id(edition_id)  # Ищем издание по ID
        if edition.status != LibraryStatus.RESERVED:  # Снять можно только существующую бронь
            raise InvalidStateError(f"Издание не забронировано. Текущий статус: '{edition.status.value}'.")
        edition.status = LibraryStatus.AVAILABLE  # Возвращаем издание на полку
        edition.due_date = None  # Бронь больше не действует
        return f"Бронирование издания '{edition.title}' отменено."

    @log_call  # Фиксирует в консоли запуск алгоритма проверки должников по срокам
    @measure_time  # Измеряет время фильтрации просроченных материалов среди всей коллекции
    def find_overdue_editions(self) -> List[LibraryEdition]:  # Доп. операция 3: поиск просроченных выдач по ТЗ
        current_date = date.today()  # Фиксируем сегодняшнюю календарную дату компьютерной системы
        overdue = [  # Собираем список нарушителей с помощью включения списков (list comprehension)
            ed for ed in self.editions   # Перебираем фонд и берем только те материалы, которые:
            if ed.status == LibraryStatus.ISSUED and ed.due_date and ed.due_date < current_date  # выданы и уже просрочены
        ]
        return overdue  # Возвращаем отфильтрованную коллекцию просроченных изданий

    @limit_calls(max_calls=5)  # Декоратор с параметром: запретит дергать тяжелую статистику чаще 5 раз
    def get_statistics(self) -> dict[str, Any]:  # Метод агрегации данных и расчета итоговых счетчиков фонда
        total = len(self.editions)  # Считаем общее число всех зарегистрированных объектов в памяти
        available = sum(1 for x in self.editions if x.status == LibraryStatus.AVAILABLE)  # Считаем доступные на полках
        issued = sum(1 for x in self.editions if x.status == LibraryStatus.ISSUED)  # Находим сумму всех выданных книг
        reserved = sum(1 for x in self.editions if x.status == LibraryStatus.RESERVED)  # Находим сумму забронированных книг
        
        overdue_count = len(self.find_overdue_editions())  # Вычисляем точное текущее количество просроченных выдач
        
        return {  # Формируем и отдаем итоговый информационный словарь для интерфейса
            "Общий фонд": total,
            "Доступно": available,
            "Выдано": issued,
            "Зарезервировано": reserved,
            "Просрочено выдач": overdue_count
        }

    def print_protocol_reports(self, reportable_objects: List[Reportable]) -> None:  # Метод демонстрации полиморфизма Protocol
        print("\n=== ВЫВОД ОТЧЕТОВ ПО ПРОТОКОЛУ (Reportable) ===")  # Печатаем визуальный заголовок в терминал
        for obj in reportable_objects:  # Перебираем циклом объекты, зная только то, что они соответствуют протоколу
            print(obj.get_report_data())  # Вызываем полиморфный метод генерации отчета, не проверяя точный класс

def inspect_object(obj: Any) -> None:  # Отдельная функция для полной интроспекции переданного объекта по ТЗ
    print("\n" + "="*30)  # Выводим верхнюю графическую границу блока анализа
    print("=== МЕХАНИЗМ ИНТРОСПЕКЦИИ ===")  # Печатаем название системного подменю
    print("1. Тип (type):", type(obj))  # Механизм 1: Получаем точный системный тип данных объекта
    print("2. Имя класса (__class__):", obj.__class__.__name__)  # Механизм 2: Достаем строго текстовое имя класса
    print("3. Проверка isinstance(obj, LibraryEdition):", isinstance(obj, LibraryEdition))  # Механизм 3: Проверка наследования
    print("4. Список атрибутов и методов (dir):", [attr for attr in dir(obj) if not attr.startswith('__')])  # Механизм 4: Получаем методы без магических
    
    print("5. Исследование сигнатур методов (inspect.signature):")  # Механизм 5: Анализируем аргументы функций
    for name, method in inspect.getmembers(obj, predicate=inspect.ismethod):  # Перебираем все внутренние методы объекта
        try:  # Открываем защитный блок try на случай работы с системными функциями
            sig = inspect.signature(method)  # С помощью модуля inspect считываем скобки и параметры метода
            print(f"   Метод: {name}{sig}")  # Выводим имя конкретной функции и типы её входящих параметров
        except Exception:  # Если сигнатуру встроенного метода прочесть не удалось
            pass  # Просто игнорируем его, продолжая полный анализ объекта
    print("="*30 + "\n")  # Выводим нижнюю графическую границу блока анализа
