import uuid
from enum import Enum
from uuid import UUID


class BookStatus(Enum):
    """
    Перечисление статусов книги.
    """
    AVAILABLE = "Доступна"
    BORROWED = "Занята"

    def __str__(self):
        """
        Переопределение строкового представления статуса.
        :return: Строковое значение статуса.
        """
        return self.value


class TableRow:
    """
    Базовый класс для строки таблицы.
    Содержит обязательное поле `id`, которое автоматически генерируется при создании объекта.
    """
    id: UUID  # Поле id для уникального идентификатора записи

    def __init__(self, **kwargs):
        """
        Инициализация строки таблицы.
        Если параметр `id` не передан, автоматически генерируется уникальный идентификатор.

        :param kwargs: Дополнительные поля записи таблицы.
        """
        if not kwargs.get('id'):
            self.id = uuid.uuid4()
        else:
            self.id = UUID(kwargs.pop('id'))
        for key, value in kwargs.items():
            setattr(self, key, value)


class Book(TableRow):
    """
    Модель данных для таблицы "Книги".
    Наследует базовый класс TableRow, добавляя поля, специфичные для книги.
    """
    name: str = None
    author_id: UUID = None
    year: int = None
    status: BookStatus = BookStatus.AVAILABLE

    def __init__(self, **kwargs):
        """
        Инициализация объекта книги.
        Преобразует статус и идентификатор автора при необходимости.

        :param kwargs: Поля книги.
        """
        if kwargs.get('status'):
            status = kwargs.pop('status')
            if isinstance(status, str):
                self.status = getattr(BookStatus, status)
            else:
                self.status = status

        if not isinstance(kwargs.get('author_id'), UUID):
            self.author_id = UUID(kwargs.pop('author_id'))

        super().__init__(**kwargs)


class Author(TableRow):
    """
    Модель данных для таблицы "Авторы".
    Наследует базовый класс TableRow, добавляя поля, специфичные для автора.
    """
    name: str = None  # Фамилия и инициалы автора


tables = [Book, Author]
"""
Список моделей данных (таблиц), используемых в базе данных.
Может применяться для автоматической инициализации и обработки данных.
"""
