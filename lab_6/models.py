from dataclasses import dataclass, field  # Подключаем автосоздание конструкторов и настройку полей
from enum import Enum                     # Подключаем инструмент для создания списков-статусов
from datetime import date                 # Подключаем работу с календарными датами
from typing import Optional               # Подключаем тип для полей, которые могут быть равны None

class LibraryStatus(Enum):                # Перечисление всех возможных статусов книги
    AVAILABLE = "доступно"                 # Статус: книга на полке в библиотеке
    ISSUED = "выдано"                     # Статус: книга на руках у читателя
    RESERVED = "зарезервировано"           # Статус: книга отложена по брони

@dataclass                                # Автоматически пишет за нас метод __init__
class LibraryEdition:                     # Наш главный базовый класс для всего фонда
    """Базовый класс dataclass для изданий."""
    id: int                               # Уникальный номер (ID) издания
    title: str                            # Название книги, журнала или файла
    status: LibraryStatus = LibraryStatus.AVAILABLE  # Статус, по умолчанию книга свободна
    
    due_date: Optional[date] = None       # Срок возврата. Заполняется только при выдаче

    # Скрытый из-за подчеркнутого имени атрибут рейтинга. field отключает его из __init__
    _internal_rating: float = field(default=5.0, init=False)

    @property                             # Геттер: делает метод rating доступным как обычное поле
    def rating(self) -> float:            # Метод для безопасного чтения скрытого рейтинга
        return self._internal_rating      # Просто возвращаем значение скрытой переменной

    @rating.setter                        # Сеттер: перехватывает и проверяет изменение рейтинга
    def rating(self, value: float) -> None:  # Метод проверки нового значения рейтинга
        if not (0.0 <= value <= 10.0):    # Если рейтинг меньше 0 или больше 10
            raise ValueError("Рейтинг должен быть в диапазоне от 0.0 до 10.0")  # Бьем тревогу
        self._internal_rating = value     # Если проверка пройдена, сохраняем значение

@dataclass                                # Генерирует конструктор для расширенных полей книги
class Book(LibraryEdition):               # Класс Книга, наследует всю базу от LibraryEdition
    """Производный класс 1: Книга."""
    author: str = "Неизвестный автор"     # Уникальное поле книги: ФИО автора
    pages: int = 0                        # Уникальное поле книги: количество страниц

    def get_report_data(self) -> str:     # Реализация обязательного метода для Protocol
        return f"Книга '{self.title}' (Автор: {self.author}, Страниц: {self.pages}, Статус: {self.status.value})"  # Строка-отчет

@dataclass                                # Генерирует конструктор для полей журнала
class Magazine(LibraryEdition):           # Класс Журнал, наследует базу от LibraryEdition
    """Производный класс 2: Журнал."""
    issue_number: int = 1                 # Уникальное поле журнала: номер выпуска
    publish_month: str = "Январь"         # Уникальное поле журнала: месяц издания

    def get_report_data(self) -> str:     # Реализация метода для Protocol (полиморфизм)
        return f"Журнал '{self.title}' (Выпуск №{self.issue_number}, Месяц: {self.publish_month}, Статус: {self.status.value})"  # Строка-отчет

@dataclass                                # Генерирует конструктор для полей электронного издания
class DigitalEdition(LibraryEdition):     # Класс Электронное издание, наследует базу
    """Производный класс 3: Электронное издание (ТРЕБОВАНИЕ ТЗ)."""
    file_format: str = "PDF"              # Уникальное поле файла: формат (PDF/EPUB)
    file_size_mb: float = 0.0             # Уникальное поле файла: размер в мегабайтах

    def get_report_data(self) -> str:     # Реализация метода для Protocol (полиморфизм)
        return f"Электронное издание '{self.title}' (Формат: {self.file_format}, Размер: {self.file_size_mb} MB, Status: {self.status.value})"  # Строка-отчет
