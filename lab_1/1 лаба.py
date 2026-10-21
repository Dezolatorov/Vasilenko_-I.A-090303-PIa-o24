def check():  # ввод и проверка данных
    while True:
        staff = int(input('Введите число сотрудников: '))
        if staff <= 0:
            print('Ошибка: Количество сотрудников должно быть больше 0.')
            continue
        break
    total_list = []  # список введённых окладов
    
    for i in range(staff):  # для каждого сотрудника вводим оклад
        while True:
            money = float(input(f'Введите оклад для {i+1} сотрудника: '))
            if money < 0:
                print('Ошибка: Оклад не может быть отрицательным!')
                continue
            total_list.append(money)  # добавление оклада в список 
            break
    return total_list


def analyze_results(total_list1):  # рассчёт и вывод з/п
    average_money = sum(total_list1) / len(total_list1)
    max_money = max(total_list1)
    min_money = min(total_list1)
    fond = sum(total_list1)
    
    count_staff = 0  # пока сотрудники с з/п выше среднего 0
    for j in total_list1:  # проходимся по каждому значению из списка окладов 
        if j > average_money:  # если текущ з/п в списке больше ср. знач, то +1
            count_staff += 1

    print('Средняя з/п: ', round(average_money, 2))  # округлил до 2-х знаков после запятой
    print('Максимальная з/п: ', max_money)
    print('Минимальная  з/п: ', min_money)
    print('Количество сотрудников, получающих з/п больше среднего: ', count_staff)
    print('Фонд заработной платы: ', fond)
    
    if average_money < 30000:  # условная конструкция определения уровня дохода
        print('Уровень средней з/п: Низкий уровень дохода')
    elif average_money < 50000:
        print('Уровень средней з/п: Средний уровень дохода')
    else:
        print('Уровень средней з/п: Высокий уровень дохода')


def main():  # главная функция, которая запускает программу
    tatal_list = check()  # окончательный список з/п
    analyze_results(tatal_list)  # ср, макс, мин з/п и.т.д


if __name__ == '__main__':  # файл запущен напрямую, а не импортирован
    main()
