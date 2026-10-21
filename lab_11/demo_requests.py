import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def print_response(title, response):
    print(f"\n=== {title} ===")
    print(f"Status Code: {response.status_code}")
    try:
        # Красивый вывод JSON
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception:
        print("No JSON response")

print("Запуск тестовых запросов к API...")

# 1. Выдача книги (берем ID=1, читатель ID=2)
res_borrow = requests.post(f"{BASE_URL}/books/1/borrow", json={"reader_id": 2, "days": 14})
print_response("1. Транзакционная выдача книги", res_borrow)

# 2. Возврат книги (если выдача прошла успешно, берем ID выдачи)
if res_borrow.status_code == 201:
    loan_id = res_borrow.json().get("id")
    res_return = requests.post(f"{BASE_URL}/loans/{loan_id}/return")
    print_response("2. Возврат книги", res_return)

# 3. Поиск книг (запишется в историю Redis)
res_search = requests.get(f"{BASE_URL}/books/search", params={"q": "Пушкин"})
print_response("3. Поиск книг (логируется в Redis)", res_search)

# 4. Удаление книги (создадим новую и удалим её)
new_book = {"title": "Книга на удаление", "author_id": 1, "genre_id": 1, "year": 2020, "price": 100, "copies_total": 1}
res_create = requests.post(f"{BASE_URL}/books", json=new_book)
book_id = res_create.json()["id"]

res_delete = requests.delete(f"{BASE_URL}/books/{book_id}")
print(f"\n=== 4. Удаление книги (ID: {book_id}) ===")
print(f"Status Code: {res_delete.status_code} (Ожидается 204)")

# 5. Проверка 404 (запрос удаленной книги)
res_404 = requests.get(f"{BASE_URL}/books/{book_id}")
print_response(f"5. Проверка 404 для удаленной книги (ID: {book_id})", res_404)