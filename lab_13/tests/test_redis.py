from app.cache import BookCache


def test_set_and_get_json(cache: BookCache):
    cache.put_book("abc123", {"_id": "abc123", "title": "Тест"})
    stored = cache.get_book("abc123")

    assert stored is not None
    assert stored["title"] == "Тест"


def test_ttl_is_set_for_cached_book(cache: BookCache):
    cache.put_book("abc123", {"_id": "abc123", "title": "Тест"})
    ttl = cache.book_ttl("abc123")

    assert 0 < ttl <= 300


def test_search_history_is_a_list_with_limit(cache: BookCache):
    for index in range(12):
        cache.record_search(f"запрос-{index}")

    history = cache.search_history()
    assert len(history) == 10
    assert history[0] == "запрос-11"
    assert history[-1] == "запрос-2"


def test_popular_books_sorted_set(cache: BookCache):
    cache.register_view("id1", "Дюна", "Фантастика")
    cache.register_view("id1", "Дюна", "Фантастика")
    cache.register_view("id2", "1984", "Роман")

    popular = cache.popular_books(3)
    assert popular[0] == {"title": "Дюна", "views": 2}
    assert popular[1]["title"] == "1984"


def test_genre_views_hash(cache: BookCache):
    cache.register_view("id1", "Дюна", "Фантастика")
    cache.register_view("id2", "1984", "Роман")
    cache.register_view("id3", "Солярис", "Фантастика")

    assert cache.genre_views() == {"Фантастика": "2", "Роман": "1"}


def test_invalidate_removes_key(cache: BookCache):
    cache.put_book("abc123", {"_id": "abc123", "title": "Тест"})
    assert cache.get_book("abc123") is not None

    cache.invalidate_book("abc123")
    assert cache.get_book("abc123") is None
    assert cache.book_ttl("abc123") == -2
