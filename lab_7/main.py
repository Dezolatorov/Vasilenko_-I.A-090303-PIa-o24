# main.py
from infrastructure import InMemoryLibraryRepository, EmailSender, SmsSender
from services import LibraryService
from console_ui import ConsoleUI

def main():
    # Инициализируем инфраструктуру (компоненты низкого уровня)
    repository = InMemoryLibraryRepository()
    
    # Мы можем легко переключать стратегии извещения, меняя одну строчку кода! (Реализация OCP)
    notifier = EmailSender()  # Либо SmsSender()
    
    # Собираем сервис, внедряя зависимости (DIP)
    library_service = LibraryService(repository=repository, notifier=notifier)
    
    # Запускаем интерфейс
    ui = ConsoleUI(service=library_service)
    ui.run()

if __name__ == "__main__":
    main()
