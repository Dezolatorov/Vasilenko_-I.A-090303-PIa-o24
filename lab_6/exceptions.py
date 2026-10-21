class LibraryError(Exception):  # Наш главный базовый класс ошибки, созданный по ТЗ Базовое исключение для библиотеки
    pass  # Заглушка, чтобы пустой класс работал без ошибок

class EntityNotFoundError(LibraryError):  # Ошибка: срабатывает, если ввели несуществующий ID Исключение: объект не найден
    pass

class InvalidStateError(LibraryError):  # Ошибка: нельзя выдать уже выданную книгу
    pass