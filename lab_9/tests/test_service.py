import pytest
from service import CalculatorService
from repository import CalculationRepository
from exceptions import CalculationError, CalculationNotFoundError


@pytest.fixture
def service():
    return CalculatorService(CalculationRepository())


# --------- Позитивные сценарии ---------
def test_simple_addition(service):
    assert service.calculate("2+2").result == 4.0


def test_operator_precedence(service):
    assert service.calculate("2+3*4").result == 14.0


def test_power(service):
    assert service.calculate("2^10").result == 1024.0


def test_float_division(service):
    assert service.calculate("10/4").result == 2.5


def test_parentheses(service):
    assert service.calculate("(2+3)*4").result == 20.0


def test_negative_numbers(service):
    assert service.calculate("-5+10").result == 5.0


# --------- Отрицательные сценарии ---------
def test_empty_expression(service):
    with pytest.raises(CalculationError):
        service.calculate("")


def test_division_by_zero(service):
    with pytest.raises(CalculationError):
        service.calculate("5/0")


def test_invalid_characters(service):
    with pytest.raises(CalculationError):
        service.calculate("__import__('os').system('ls')")


def test_double_operator(service):
    with pytest.raises(CalculationError):
        service.calculate("2++2")


# --------- CRUD через сервис ---------
def test_get_not_found(service):
    with pytest.raises(CalculationNotFoundError):
        service.get(999)


def test_delete_not_found(service):
    with pytest.raises(CalculationNotFoundError):
        service.delete(999)


def test_update(service):
    calc = service.calculate("1+1")
    updated = service.update(calc.id, "2*2")
    assert updated.result == 4.0


def test_history_returns_most_recent_first(service):
    for i in range(5):
        service.calculate(f"{i}+1")
    hist = service.history(3)
    assert [c.id for c in hist] == [5, 4, 3]


def test_history_bad_limit(service):
    with pytest.raises(CalculationError):
        service.history(0)


def test_clear(service):
    service.calculate("1+1")
    service.calculate("2+2")
    assert service.clear() == 2
    assert service.get_all() == []