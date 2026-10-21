from enum import Enum


class ItemType(Enum):
    PRINTED_BOOK = "printed_book"
    EBOOK = "ebook"
    MAGAZINE = "magazine"


class ItemStatus(Enum):
    AVAILABLE = "available"
    ISSUED = "issued"
    RESERVED = "reserved"


class ReaderCategory(Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    PREFERENTIAL = "preferential"