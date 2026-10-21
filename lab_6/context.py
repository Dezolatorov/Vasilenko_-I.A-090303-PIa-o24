from contextlib import contextmanager  # Подключаем декоратор для создания контекстных менеджеров
from typing import Generator           # Подключаем аннотацию типа генератора для функций с yield

@contextmanager                        # Делает из функции полноценный контекстный менеджер для блока with
def transaction_mode(collection_name: str) -> Generator[None, None, None]:  # Функция-менеджер, принимает имя коллекции
    """Контекстный менеджер для безопасного транзакционного режима работы с коллекцией."""

    print(f"\n--- [TRANSACTION START] Открыт транзакционный режим для: '{collection_name}' ---")  # Срабатывает при входе в with (имитация BEGIN)

    try:                               # Начинаем отслеживать ошибки внутри блока с кодом
        yield                          # Замораживает менеджер и передает управление коду внутри with в main.py
        print(f"--- [TRANSACTION SUCCESS] Все операции в '{collection_name}' успешно зафиксированы ---")  # Срабатывает, если все успешно (имитация COMMIT)
    except Exception as e:             # Перехватываем любую ошибку, если в блоке с кодом случилась авария
        print(f"--- [TRANSACTION ROLLBACK] Ошибка внутри транзакции '{collection_name}': {type(e).__name__}. Откат изменений! ---")  # Сообщаем об откате (имитация ROLLBACK)
        raise                          # Пробрасываем ошибку дальше в main.py для корректной остановки
    finally:                           # Блок, который выполнится при любом исходе транзакции
        print(f"--- [TRANSACTION END] Сессия работы с '{collection_name}' закрыта ---\n")  # Освобождаем ресурсы и закрываем сессию
