import services
import storage
from exceptions import salaryError

def main():
    employees = storage.load_from_json() #При старте программы автоматически загружаем сотрудников из JSON
    print(f"Добро пожаловать! Загружено сотрудников из базы: {len(employees)}")

    while True:
        print("\n===== МЕНЮ УЧЕТА СОТРУДНИКОВ =====")
        print("1. Показать всех сотрудников")
        print("2. Добавить сотрудника")
        print("3. Удалить сотрудника")
        print("4. Найти сотрудника (по ФИО или отделу)")
        print("5. Показать статистику зарплат")
        print("6. Изменить зарплату сотрудника")
        print("7. Экспорт данных в CSV")
        print("0. Выход из программы")
        
        choice = input("Выберите пункт меню: ").strip()
        
        if choice == "1":
            if not employees:
                print("Список сотрудников пуст.")
            else:
                print("\nТекущий список сотрудников:")
                for emp in employees:
                    print(emp)  # Здесь автоматически сработает метод __str__ из класса staff
                    
        elif choice == "2":
            fullname = input("Введите ФИО сотрудника: ").strip()
            position = input("Введите должность: ").strip()
            department = input("Введите отдел: ").strip()
            salary_input = input("Введите зарплату: ").strip()
            
            try: # Ловим ошибки при вводе зарплаты
                services.add_staff(employees, fullname, position, department, salary_input)
                storage.save_to_json(employees) # Автоматически сохраняем изменения в JSON
            except ValueError:
                print("Ошибка ввода: Зарплата должна быть числом!")
            except salaryError as e:
                print(f"Ошибка бизнес-логики: {e}!")
                
        elif choice == "3":
            fullname = input("Введите ФИО сотрудника для удаления: ").strip()
            services.remove_staff(employees, fullname)
            storage.save_to_json(employees) # Сохраняем обновленный список
            
        elif choice == "4":
            search_str = input("Введите текст для поиска (имя или отдел): ").strip()
            results = services.search_staff(employees, search_str)
            if not results:
                print("Сотрудники не найдены.")
            else:
                print(f"\nНайдено сотрудников ({len(results)}):")
                for emp in results:
                    print(emp)
                    
        elif choice == "5":
            stats = services.calculate_salary_stats(employees)
            if not stats:
                print("Нет данных для расчета статистики.")
            else:
                print("\n--- Статистика по зарплатам ---")
                print(f"Общий фонд оплаты труда: {stats['total']} руб.")
                print(f"Средняя зарплата: {stats['average']:.2f} руб.") # Выводим среднюю зарплату с округлением до 2 знаков
                print(f"Максимальная зарплата: {stats['max']} руб.")
                print(f"Минимальная зарплата: {stats['min']} руб.")
                
        elif choice == "6":
            fullname = input("Введите ФИО сотрудника: ").strip()
            salary_input = input("Введите новую зарплату: ").strip()
            try: # Ловим ошибки при вводе новой зарплаты
                if services.change_salary(employees, fullname, salary_input):
                    storage.save_to_json(employees) # Сохраняем изменения в JSON
            except ValueError:
                print("Ошибка ввода: Зарплата должна быть числом!")
            except salaryError as e:
                print(f"Ошибка бизнес-логики: {e}!")

        elif choice == "7":
            storage.export_to_csv(employees)
            print("Данные успешно сохранены в файл employees.csv!")
            
        elif choice == "0":
            print("Программа успешно завершена. Всего доброго!")
            break
            
        else:
            print("Ошибка: Неизвестный пункт меню. Пожалуйста, выберите число от 0 до 7.")

if __name__ == "__main__":# Проверка: если этот файл запускают как главный, а не импортируют куда-то
    main()# Запускаем нашу самую первую функцию main() и стартуем меню