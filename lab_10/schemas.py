"""Проверка входных данных и разбор параметров запроса."""

from exceptions import BadRequestError, ValidationError

REQUIRED_FIELDS: tuple[str, ...] = ("title", "author", "genre", "year", "price", "available")
ALL_FIELDS: tuple[str, ...] = REQUIRED_FIELDS

FILTER_FIELDS: tuple[str, ...] = ("author", "genre", "available", "min_price", "max_price", "year_from", "year_to")
SORT_FIELDS: tuple[str, ...] = ("title", "author", "genre", "year", "price", "available")
ORDERS: tuple[str, ...] = ("asc", "desc")

MAX_YEAR: int = 2100


def _as_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"Field '{field}' must be an integer")
    return value


def _as_float(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"Field '{field}' must be a number")
    return float(value)


def _as_text(value: object, field: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"Field '{field}' must be a string")
    text = value.strip()
    if not text and not allow_empty:
        raise ValidationError(f"Field '{field}' must not be empty")
    return text


def validate_book(data: object, partial: bool = False) -> dict:
    """Проверить тело запроса и вернуть нормализованные поля книги.

    partial=True соответствует PATCH: передаются только изменяемые поля.
    """
    if not isinstance(data, dict):
        raise BadRequestError("Request body must be a JSON object")

    unknown = sorted(set(data) - set(ALL_FIELDS))
    if unknown:
        raise ValidationError(f"Unknown fields: {', '.join(unknown)}")

    if not partial:
        missing = [field for field in REQUIRED_FIELDS if field not in data]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    if partial and not data:
        raise ValidationError("Request body must contain at least one field")

    result: dict = {}

    if "title" in data:
        result["title"] = _as_text(data["title"], "title")
    if "author" in data:
        result["author"] = _as_text(data["author"], "author")
    if "genre" in data:
        result["genre"] = _as_text(data["genre"], "genre")

    if "year" in data:
        year = _as_int(data["year"], "year")
        if not 1 <= year <= MAX_YEAR:
            raise ValidationError(f"Field 'year' must be between 1 and {MAX_YEAR}")
        result["year"] = year

    if "price" in data:
        price = _as_float(data["price"], "price")
        if price <= 0:
            raise ValidationError("Field 'price' must be greater than 0")
        result["price"] = round(price, 2)

    if "available" in data:
        available = _as_int(data["available"], "available")
        if available < 0:
            raise ValidationError("Field 'available' must be greater than or equal to 0")
        result["available"] = available

    return result


def parse_filters(params: dict) -> dict:
    """Разобрать query-параметры фильтрации."""
    filters: dict = {}

    for field in ("author", "genre"):
        value = params.get(field)
        if value:
            filters[field] = value.strip().lower()

    value = params.get("available")
    if value is not None and value != "":
        lowered = value.strip().lower()
        if lowered not in ("true", "false", "1", "0"):
            raise ValidationError("Query parameter 'available' must be true or false")
        filters["available"] = lowered in ("true", "1")

    for field in ("min_price", "max_price"):
        value = params.get(field)
        if value is not None and value != "":
            try:
                filters[field] = float(value)
            except ValueError as error:
                raise ValidationError(f"Query parameter '{field}' must be a number") from error

    if "min_price" in filters and "max_price" in filters and filters["min_price"] > filters["max_price"]:
        raise ValidationError("Parameter 'min_price' must not exceed 'max_price'")

    for field in ("year_from", "year_to"):
        value = params.get(field)
        if value is not None and value != "":
            try:
                filters[field] = int(value)
            except ValueError as error:
                raise ValidationError(f"Query parameter '{field}' must be an integer") from error

    if "year_from" in filters and "year_to" in filters and filters["year_from"] > filters["year_to"]:
        raise ValidationError("Parameter 'year_from' must not exceed 'year_to'")

    return filters


def parse_sorting(params: dict) -> tuple[str | None, str]:
    """Проверить параметры сортировки sort и order."""
    sort_by = params.get("sort")
    if sort_by is not None and sort_by != "":
        sort_by = sort_by.strip().lower()
        if sort_by not in SORT_FIELDS:
            raise ValidationError(f"Query parameter 'sort' must be one of: {', '.join(SORT_FIELDS)}")
    else:
        sort_by = None

    order = (params.get("order") or "asc").strip().lower()
    if order not in ORDERS:
        raise ValidationError("Query parameter 'order' must be asc or desc")

    return sort_by, order


def parse_book_id(raw_id: str) -> int:
    """Проверить path-параметр идентификатора книги."""
    try:
        book_id = int(raw_id)
    except (TypeError, ValueError) as error:
        raise BadRequestError(f"Identifier must be an integer, got '{raw_id}'") from error
    if book_id <= 0:
        raise BadRequestError("Identifier must be a positive integer")
    return book_id
