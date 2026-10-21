-- 15 обязательных SQL-запросов к БД «Библиотека».
-- Файл используется скриптом demo_sql.py: каждый запрос печатается вместе с результатом.

-- 1. SELECT: все книги
SELECT id, title, genre, year, price FROM books ORDER BY id;

-- 2. WHERE: книги дешевле 600 рублей и не антиутопии
SELECT title, genre, price
FROM books
WHERE price < 600 AND genre <> 'антиутопия'
ORDER BY price;

-- 3. ORDER BY: сортировка фонда по цене по убыванию
SELECT title, price
FROM books
ORDER BY price DESC, title ASC;

-- 4. JOIN: книги вместе с авторами (связь 1:N)
SELECT b.title, a.full_name, a.country
FROM books AS b
JOIN authors AS a ON a.id = b.author_id
ORDER BY a.full_name, b.title;

-- 5. LEFT JOIN: читатели и количество взятых книг (включая читателей без выдач)
SELECT r.full_name, COUNT(l.id) AS loans_count
FROM readers AS r
LEFT JOIN loans AS l ON l.reader_id = r.id
GROUP BY r.id, r.full_name
ORDER BY loans_count DESC, r.full_name;

-- 6. GROUP BY: количество книг по жанрам
SELECT genre, COUNT(*) AS books_count
FROM books
GROUP BY genre
ORDER BY books_count DESC, genre;

-- 7. HAVING: авторы, у которых больше двух книг в фонде
SELECT a.full_name, COUNT(b.id) AS books_count
FROM authors AS a
JOIN books AS b ON b.author_id = a.id
GROUP BY a.id, a.full_name
HAVING COUNT(b.id) > 2
ORDER BY books_count DESC;

-- 8. COUNT: сколько выдач ещё не возвращено
SELECT COUNT(*) AS active_loans
FROM loans
WHERE returned_at IS NULL;

-- 9. AVG / SUM: средняя цена книги и суммарная стоимость фонда
SELECT ROUND(AVG(price), 2) AS avg_price, SUM(price * total_copies) AS fund_value
FROM books;

-- 10. Подзапрос: книги дороже средней цены фонда
SELECT title, price
FROM books
WHERE price > (SELECT AVG(price) FROM books)
ORDER BY price DESC;

-- 11. Несколько условий + LEFT JOIN: активные выдачи с просрочкой на дату 2025-10-19
SELECT r.full_name, b.title, l.due_at
FROM loans AS l
JOIN books AS b   ON b.id = l.book_id
JOIN readers AS r ON r.id = l.reader_id
WHERE l.returned_at IS NULL
  AND l.due_at < '2025-10-19'
ORDER BY l.due_at;

-- 12. Связь нескольких таблиц (books + authors + tags через промежуточную таблицу)
SELECT b.title, a.full_name, t.name AS tag
FROM books AS b
JOIN authors AS a    ON a.id = b.author_id
JOIN book_tags AS bt ON bt.book_id = b.id
JOIN tags AS t       ON t.id = bt.tag_id
WHERE t.name = 'фантастика'
ORDER BY b.title;

-- 13. INSERT: новый читатель
INSERT INTO readers (full_name, email, phone, registered_at)
VALUES ('Орлова Анна Павловна', 'orlova@example.com', '+7-900-666-77-88', '2026-01-12');

-- 14. UPDATE: повышение цены книг заданного жанра (антиутопии подорожали на 10%)
UPDATE books
SET price = ROUND(price * 1.1, 2)
WHERE genre = 'антиутопия';

-- 15. DELETE: удаление читателя, который не брал книг
DELETE FROM readers
WHERE id = (SELECT r.id
            FROM readers AS r
            LEFT JOIN loans AS l ON l.reader_id = r.id
            WHERE l.id IS NULL
            ORDER BY r.id DESC
            LIMIT 1);
