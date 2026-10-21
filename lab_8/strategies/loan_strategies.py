from models.entities import Reader
from models.enums import ReaderCategory


class StandardLoanStrategy:
    name = "standard"

    def calculate_days(self, reader: Reader) -> int:
        return 14


class PreferentialLoanStrategy:
    name = "preferential"

    def calculate_days(self, reader: Reader) -> int:
        if reader.category == ReaderCategory.PREFERENTIAL:
            return 30
        return 14


class TeacherLoanStrategy:
    name = "teacher"

    def calculate_days(self, reader: Reader) -> int:
        if reader.category == ReaderCategory.TEACHER:
            return 60
        return 14


def strategy_for_reader(reader: Reader):
    if reader.category == ReaderCategory.TEACHER:
        return TeacherLoanStrategy()
    if reader.category == ReaderCategory.PREFERENTIAL:
        return PreferentialLoanStrategy()
    return StandardLoanStrategy()