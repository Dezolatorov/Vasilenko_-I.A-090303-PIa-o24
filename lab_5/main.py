import sys
from models import Employee, Manager
from operations import (
    filter_objects, transform_objects, sort_objects,
    find_max_salary, has_department, all_salaries_positive,
    get_positions, total_salary, make_salary_filter, make_department_filter
)
from generators import employee_generator, EmployeeIterator


employees = [
    Employee("Иванов Иван", "IT", "Программист", 80000),
    Employee("Петрова Анна", "HR", "Менеджер по персоналу", 60000),
    Manager("Сидоров Пётр", "IT", "Тимлид", 120000, 30000),
    Employee("Козлов Дмитрий", "IT", "Тестировщик", 70000),
    Employee("Смирнова Елена", "Бухгалтерия", "Бухгалтер", 55000),
    Manager("Морозов Алексей", "Sales", "Руководитель отдела", 100000, 20000),
]


def print_employees(obj_list):
    if not obj_list:
        print("Нет сотрудников для отображения.")
        return
    for i, emp in enumerate(obj_list, 1):
        print(f"{i}. {emp}")


def main():
    while True:
        print("\n===== МЕНЮ =====")
        print("1. Показать всех сотрудников")
        print("2. Отфильтровать по зарплате (больше заданной)")
        print("3. Получить список должностей (map)")
        print("4. Отсортировать по зарплате")
        print("5. Найти самого высокооплачиваемого")
        print("6. Проверить наличие отдела (any)")
        print("7. Проверить, что все зарплаты положительные (all)")
        print("8. Генератор сотрудников отдела")
        print("9. Демонстрация собственного итератора")
        print("10. Демонстрация ленивости (список vs генератор)")
        print("11. Общая сумма зарплат (reduce)")
        print("12. Сотрудники отдела (замыкание + map)")
        print("0. Выход")
        choice = input("Ваш выбор: ")

        try:
            if choice == "1":
                print_employees(employees)

            elif choice == "2":
                min_salary = float(input("Введите минимальную зарплату: "))
                salary_filter = make_salary_filter(min_salary) #замыкание запомнило порог
                filtered = list(filter_objects(employees, salary_filter))
                print_employees(filtered)

            elif choice == "3":
                positions = get_positions(employees)
                print("Должности:", positions)

            elif choice == "4":
                sorted_emps = sort_objects(employees, key_function=lambda e: e.salary)
                print_employees(sorted_emps)

            elif choice == "5":
                best = find_max_salary(employees)
                if best:
                    print("Самый высокооплачиваемый:", best)
                else:
                    print("Список пуст.")

            elif choice == "6":
                dept = input("Введите название отдела: ")
                if has_department(employees, dept):
                    print(f"В отделе '{dept}' есть сотрудники.")
                else:
                    print(f"В отделе '{dept}' нет сотрудников.")

            elif choice == "7":
                if all_salaries_positive(employees):
                    print("Все зарплаты положительные.")
                else:
                    print("Есть сотрудники с неположительной зарплатой!")

            elif choice == "8":
                dept = input("Введите отдел для генератора: ")
                print(f"Сотрудники отдела '{dept}':")
                for emp in employee_generator(employees, dept):
                    print(" ", emp)

            elif choice == "9":
                print("Перебор через собственный итератор:")
                iterator = EmployeeIterator(employees)
                for emp in iterator:
                    print(" ", emp)

            elif choice == "10":
                print("Создаём список из 1_000_000 квадратов...")
                list_result = [x * x for x in range(1_000_000)]
                print("Размер списка в памяти (байт):", sys.getsizeof(list_result))

                print("Создаём генератор из 1_000_000 квадратов...")
                gen_result = (x * x for x in range(1_000_000))
                print("Размер генератора в памяти (байт):", sys.getsizeof(gen_result))
                print("Генератор не хранит все значения сразу!")

            elif choice == "11":
                total = total_salary(employees)
                print(f"Общая сумма зарплат: {total}")

            elif choice == "12":
                dept = input("Введите отдел: ")
                dept_filter = make_department_filter(dept) #второе замыкание — предикат по отделу
                found = list(filter_objects(employees, dept_filter))
                if not found:
                    print(f"В отделе '{dept}' нет сотрудников.")
                else:
                    names = list(transform_objects(found, lambda e: e.name)) #map: оставляем только имена
                    print(f"Сотрудники отдела '{dept}' ({len(found)}):")
                    for name in names:
                        print(" ", name)

            elif choice == "0":
                print("Выход из программы.")
                break

            else:
                print("Неизвестный пункт меню. Попробуйте снова.")

        except ValueError:
            print("Ошибка: введено некорректное значение. Пожалуйста, введите число.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    main()