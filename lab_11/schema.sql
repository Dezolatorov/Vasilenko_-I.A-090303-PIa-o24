-- Схема базы данных «Библиотека» (вариант 2).
-- СУБД: SQLite 3. Схема приведена к 3-й нормальной форме.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS book_tags;
DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS readers;
DROP TABLE IF EXISTS authors;

-- Авторы: одна запись описывает автора один раз (устранено дублирование ФИО в books).
CREATE TABLE authors (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT    NOT NULL UNIQUE,
    country   TEXT    NOT NULL
);

-- Книги библиотечного фонда. author_id — внешний ключ на authors (связь 1:N).
CREATE TABLE books (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT    NOT NULL CHECK (length(trim(title)) > 0),
    author_id        INTEGER NOT NULL,
    genre            TEXT    NOT NULL,
    year             INTEGER NOT NULL CHECK (year BETWEEN 1 AND 2100),
    price            REAL    NOT NULL CHECK (price > 0),
    total_copies     INTEGER NOT NULL CHECK (total_copies >= 0),
    available_copies INTEGER NOT NULL CHECK (available_copies >= 0),
    cover_path       TEXT,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE RESTRICT,
    CHECK (available_copies <= total_copies)
);

-- Читатели. email уникален: один читатель — одна учётная запись.
CREATE TABLE readers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT NOT NULL CHECK (length(trim(full_name)) > 0),
    email         TEXT NOT NULL UNIQUE,
    phone         TEXT,
    registered_at TEXT NOT NULL
);

-- Выдачи книг: связь books 1:N loans и readers 1:N loans.
-- returned_at = NULL означает, что книга ещё на руках.
CREATE TABLE loans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id     INTEGER NOT NULL,
    reader_id   INTEGER NOT NULL,
    taken_at    TEXT    NOT NULL,
    due_at      TEXT    NOT NULL,
    returned_at TEXT,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE RESTRICT,
    CHECK (due_at >= taken_at)
);

-- Теги произведений (справочник для связи N:M).
CREATE TABLE tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Промежуточная таблица связи N:M между книгами и тегами.
CREATE TABLE book_tags (
    book_id INTEGER NOT NULL,
    tag_id  INTEGER NOT NULL,
    PRIMARY KEY (book_id, tag_id),
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id)  REFERENCES tags(id)  ON DELETE CASCADE
);

-- Индексы (этап 5).
-- 1. Поиск книги по названию: WHERE title LIKE 'Война%' и ORDER BY title.
CREATE INDEX idx_books_title ON books(title);

-- 2. Фильтрация и группировка по автору: JOIN authors / WHERE author_id = ?.
CREATE INDEX idx_books_author ON books(author_id);

-- 3. Поиск активных выдач читателя: WHERE reader_id = ? AND returned_at IS NULL.
CREATE INDEX idx_loans_reader ON loans(reader_id, returned_at);

-- 4. Проверка, свободна ли книга: WHERE book_id = ? AND returned_at IS NULL.
CREATE INDEX idx_loans_book ON loans(book_id, returned_at);

-- 5. Обратная выборка тегов книги для связи N:M.
CREATE INDEX idx_book_tags_tag ON book_tags(tag_id);
