from repository import CalculationRepository


def test_add_and_get():
    repo = CalculationRepository()
    calc = repo.add("2+2", 4.0)
    assert calc.id == 1
    assert repo.get(1).result == 4.0


def test_ids_are_unique():
    repo = CalculationRepository()
    a = repo.add("1+1", 2.0)
    b = repo.add("2+2", 4.0)
    assert a.id != b.id


def test_get_all():
    repo = CalculationRepository()
    repo.add("1+1", 2.0)
    repo.add("2+2", 4.0)
    assert len(repo.get_all()) == 2


def test_update_existing():
    repo = CalculationRepository()
    calc = repo.add("2+2", 4.0)
    updated = repo.update(calc.id, "3+3", 6.0)
    assert updated.expression == "3+3"
    assert updated.result == 6.0


def test_update_missing_returns_none():
    repo = CalculationRepository()
    assert repo.update(999, "1+1", 2.0) is None


def test_delete_existing():
    repo = CalculationRepository()
    calc = repo.add("2+2", 4.0)
    assert repo.delete(calc.id) is True
    assert repo.get(calc.id) is None


def test_delete_missing():
    repo = CalculationRepository()
    assert repo.delete(999) is False


def test_clear_resets_ids():
    repo = CalculationRepository()
    repo.add("1", 1.0)
    repo.add("2", 2.0)
    assert repo.clear() == 2
    assert repo.get_all() == []
    assert repo.add("3", 3.0).id == 1