"""Проверка входных данных и разбор параметров запроса."""

from exceptions import BadRequestError, ValidationError

BOOK_FIELDS: tuple[str, ...] = ("title", "author_id", "genre", "year", "price", "total_copies", "available_copies")
BOOK_REQUIRED: tuple[str, ...] = ("title", "author_id", "genre", "year", "price", "total_copies")

FILTER_FIELDS: tuple[str, ...] = (
    "author_id", "author", "genre", "tag", "q",
    "available", "min_price", "max_price", "year_from", "year_to",
)
SORT_FIELDS: tuple[str, ...] = ("title", "author", "genre", "year", "price", "total_copies", "available_copies")
ORDERS: tuple[str, ...] = ("asc", "desc")

MAX_YEAR: int = 2100
MAX_COPIES: int = 1000


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
    """Проверить тело запроса и вернуть нормализованные поля книги."""
    if not isinstance(data, dict):
        raise BadRequestError("Request body must be a JSON object")

    unknown = sorted(set(data) - set(BOOK_FIELDS))
    if unknown:
        raise ValidationError(f"Unknown fields: {', '.join(unknown)}")

    if not partial:
        missing = [field for field in BOOK_REQUIRED if field not in data]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    if partial and not data:
        raise ValidationError("Request body must contain at least one field")

    result: dict = {}

    if "title" in data:
        result["title"] = _as_text(data["title"], "title")
    if "genre" in data:
        result["genre"] = _as_text(data["genre"], "genre")

    if "author_id" in data:
        author_id = _as_int(data["author_id"], "author_id")
        if author_id <= 0:
            raise ValidationError("Field 'author_id' must be a positive integer")
        result["author_id"] = author_id

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

    for field in ("total_copies", "available_copies"):
        if field in data:
            copies = _as_int(data[field], field)
            if not 0 <= copies <= MAX_COPIES:
                raise ValidationError(f"Field '{field}' must be between 0 and {MAX_COPIES}")
            result[field] = copies

    if "available_copies" in result and "total_copies" in result:
        if result["available_copies"] > result["total_copies"]:
            raise ValidationError("Field 'available_copies' must not exceed 'total_copies'")

    return result


def validate_reader(data: object, partial: bool = False) -> dict:
    """Проверить тело запроса для читателя."""
    fields = ("full_name", "email", "phone")
    if not isinstance(data, dict):
        raise BadRequestError("Request body must be a JSON object")

    unknown = sorted(set(data) - set(fields))
    if unknown:
        raise ValidationError(f"Unknown fields: {', '.join(unknown)}")

    if not partial:
        missing = [field for field in ("full_name", "email") if field not in data]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    result: dict = {}
    if "full_name" in data:
        result["full_name"] = _as_text(data["full_name"], "full_name")
    if "email" in data:
        email = _as_text(data["email"], "email")
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValidationError("Field 'email' must be a valid email address")
        result["email"] = email.lower()
    if "phone" in data:
        phone = data["phone"]
        result["phone"] = None if phone is None else _as_text(phone, "phone", allow_empty=True)
    return result


def validate_loan(data: object) -> dict:
    """Проверить тело запроса на выдачу книги."""
    if not isinstance(data, dict):
        raise BadRequestError("Request body must be a JSON object")

    unknown = sorted(set(data) - {"book_id", "reader_id", "days"})
    if unknown:
        raise ValidationError(f"Unknown fields: {', '.join(unknown)}")

    missing = [field for field in ("book_id", "reader_id") if field not in data]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    book_id = _as_int(data["book_id"], "book_id")
    reader_id = _as_int(data["reader_id"], "reader_id")
    if book_id <= 0 or reader_id <= 0:
        raise ValidationError("Fields 'book_id' and 'reader_id' must be positive integers")

    days = _as_int(data.get("days", 14), "days")
    if not 1 <= days <= 90:
        raise ValidationError("Field 'days' must be between 1 and 90")

    return {"book_id": book_id, "reader_id": reader_id, "days": days}


def parse_filters(params: dict) -> dict:
    """Разобрать query-параметры фильтрации."""
    filters: dict = {}

    for field in ("author", "genre", "tag", "q"):
        value = params.get(field)
        if value:
            filters[field] = value.strip()

    value = params.get("author_id")
    if value not in (None, ""):
        try:
            filters["author_id"] = int(value)
        except ValueError as error:
            raise ValidationError("Query parameter 'author_id' must be an integer") from error

    value = params.get("available")
    if value not in (None, ""):
        lowered = value.strip().lower()
        if lowered not in ("true", "false", "1", "0"):
            raise ValidationError("Query parameter 'available' must be true or false")
        filters["available"] = lowered in ("true", "1")

    for field in ("min_price", "max_price"):
        value = params.get(field)
        if value not in (None, ""):
            try:
                filters[field] = float(value)
            except ValueError as error:
                raise ValidationError(f"Query parameter '{field}' must be a number") from error

    if "min_price" in filters and "max_price" in filters and filters["min_price"] > filters["max_price"]:
        raise ValidationError("Parameter 'min_price' must not exceed 'max_price'")

    for field in ("year_from", "year_to"):
        value = params.get(field)
        if value not in (None, ""):
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
    if sort_by not in (None, ""):
        sort_by = sort_by.strip().lower()
        if sort_by not in SORT_FIELDS:
            raise ValidationError(f"Query parameter 'sort' must be one of: {', '.join(SORT_FIELDS)}")
    else:
        sort_by = None

    order = (params.get("order") or "asc").strip().lower()
    if order not in ORDERS:
        raise ValidationError("Query parameter 'order' must be asc or desc")

    return sort_by, order


def parse_limit(params: dict, default: int = 20, maximum: int = 100) -> int:
    """Разобрать параметр limit для отчётов и истории поиска."""
    value = params.get("limit")
    if value in (None, ""):
        return default
    try:
        limit = int(value)
    except ValueError as error:
        raise ValidationError("Query parameter 'limit' must be an integer") from error
    if not 1 <= limit <= maximum:
        raise ValidationError(f"Query parameter 'limit' must be between 1 and {maximum}")
    return limit


def parse_positive_id(raw_id: str, entity: str = "resource") -> int:
    """Проверить path-параметр идентификатора."""
    try:
        identifier = int(raw_id)
    except (TypeError, ValueError) as error:
        raise BadRequestError(f"Identifier of {entity} must be an integer, got '{raw_id}'") from error
    if identifier <= 0:
        raise BadRequestError(f"Identifier of {entity} must be a positive integer")
    return identifier


def parse_search_query(params: dict) -> str:
    """Проверить поисковый запрос по названию."""
    raw = (params.get("q") or "").strip()
    if len(raw) < 2:
        raise ValidationError("Query parameter 'q' must contain at least 2 characters")
    if len(raw) > 100:
        raise ValidationError("Query parameter 'q' must not exceed 100 characters")
    return raw
