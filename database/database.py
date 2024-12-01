import json
import os.path
from enum import Enum
from os import PathLike
from typing import Dict, Union, List, Tuple
from uuid import UUID
from tables import TableRow, tables



def default_serializer(o):
    """
    Сериализатор для объектов, которые не поддерживаются стандартным JSON-сериализатором.

    :param o: Объект для сериализации.
    :return: Строковое представление объекта или сам объект, если он не требует преобразования.
    """
    if isinstance(o, UUID):
        return str(o)  # Преобразовать UUID или статус книги в строку
    elif isinstance(o, Enum):
        return o.name # Преобразует элемент Enum в строковое имя.
    else:
        return o  # Вернуть объект без изменений



class DataBase:
    """
    Простая ORM с функционалом для управления базой данных, представленной в виде JSON-файла.
    Использует шаблон Singleton для обеспечения единственного экземпляра базы данных.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, class_table: type[TableRow] = None):
        """
        Инициализация базы данных.

        :param class_table: Класс, представляющий таблицу.
        :raises Exception: Если таблица не указана.
        """
        if not self._db:
            self._db = {}
        if not class_table:
            raise Exception('Передайте таблицу для работы')
        self._current_table_name = str(class_table.__name__.lower())
        self._current_table = self._db.get(self._current_table_name)

    # Статические переменные базы данных
    _db: Dict[str, List[TableRow]] | None = None  # Словарь для хранения данных таблиц
    _db_name: str | None = None  # Имя файла базы данных
    _current_table: List[TableRow] | None = None  # Текущая таблица
    _current_table_name: str | None = None  # Имя текущей таблицы
    _results: List[TableRow] | None = None  # Результаты фильтрации данных

    @classmethod
    def init_db(cls, db_name: Union[str, PathLike]) -> None:
        """
        Инициализирует базу данных.

        :param db_name: Имя файла JSON для хранения данных.
        """
        cls._db = {}
        cls._db_name = db_name
        if not os.path.exists(cls._db_name):
            for table in tables:
                table_name = str(table.__name__.lower())
                cls._db[table_name] = []
            cls.save_db()
        else:
            with open(db_name, 'r') as file:
                data = json.loads(file.read())
                for table in tables:
                    table_name = str(table.__name__.lower())
                    table_data = data.get(table_name)
                    fields = table_data.pop(0)
                    cls._db[table_name] = []
                    for row in table_data:
                        kwargs = {}
                        col = 0
                        for field in fields:
                            kwargs[field] = row[col]
                            col += 1
                        row_object = table(**kwargs)
                        cls._db[table_name].append(row_object)



    @classmethod
    def save_db(cls):
        """
        Сохраняет данные базы данных в файл JSON.
        """
        result = {}
        for table in tables:
            table_name = str(table.__name__.lower())
            result[table_name] = []
            fields = ['id'] + list(table.__annotations__.keys())
            result[table_name].append(fields)
            for row in cls._db[table_name]:
                row_values = []
                for field in fields:
                    row_values.append(getattr(row, field, None))
                result[table_name].append(row_values)
        with open(cls._db_name, 'w') as file:
            file.write(json.dumps(result, default=default_serializer))

    def _save_table(self):
        """
        Сохраняет изменения в текущей таблице.
        """
        self._db[self._current_table_name] = self._current_table

    def filter(self, **kwargs) -> List[TableRow]:
        """
        Фильтрует записи текущей таблицы по указанным условиям.

        :param kwargs: Поля и их значения для фильтрации.
        :return: Список записей, соответствующих условиям.
        """
        self._results = self._current_table
        for field_name, value in kwargs.items():
            if callable(value):
                filter_func = lambda item: item is not None and value(getattr(item, field_name, None))
            else:
                if not isinstance(value, (List, Tuple)):
                    value = [value]
                filter_func = lambda item: getattr(item, field_name, None) in value
            self._results = list(filter(filter_func, self._results))
        return self._results

    def add(self, record: Union[List[TableRow], TableRow]):
        """
        Добавляет записи в таблицу.

        :param record: Одна запись или список записей.
        """
        if not isinstance(record, List):
            record = [record]
        self._current_table.extend(record)
        self._save_table()

    # Обновление записи по ID
    def update(self, _id: UUID, **kwargs) -> TableRow:
        """
        Обновляет запись по ID.

        :param _id: Идентификатор записи.
        :param kwargs: Поля и их новые значения.
        :return: Обновленная запись.
        :raises Exception: Если запись не найдена.
        """
        new_row = self.filter(id=_id)
        if not new_row:
            raise Exception('Запись не найдена')
        new_row = new_row[0]
        for field_name, value in kwargs.items():
            setattr(new_row, field_name, value)
        new_table = []
        for row in self._current_table:
            new_table.append(row if row.id != _id else new_row)
        self._current_table = new_table
        self._save_table()
        return new_row

    def delete(self, _id: UUID):
        """
        Удаляет записи по ID.

        :param _id: Идентификатор записи или список идентификаторов.
        """
        if not isinstance(_id, List):  # Если удаляется одна запись
            _id = [_id]
        value = lambda item: item.id not in _id  # Условие фильтрации
        self._current_table = list(filter(value, self._current_table))
        self._save_table()

    # объединения таблиц
    def join(
            self,
            other_table_class: type[TableRow],
            join_field_self: str | None = None,
            join_field_other: str | None = None
    ):
        """
        Выполняет соединение текущей таблицы с другой таблицей по полю.

        :param other_table_class: Класс другой таблицы.
        :param join_field_self: Поле для соединения в текущей таблице.
        :param join_field_other: Поле для соединения в другой таблице.
        """

        if self._current_table is None:
            raise Exception('Текущая таблица не выбрана.')

        other_table_name = other_table_class.__name__.lower()
        if other_table_name not in self._db:
            raise Exception(f'Таблица {other_table_name} не найдена.')

        if not join_field_self:
            join_field_self = f'{other_table_name}_id'
        if not join_field_other:
            join_field_other = 'id'

        # Соединение данных
        other_table = self._db.get(other_table_name)
        other_table_dict = {row.id: row for row in other_table}
        other_fields = list(other_table[0].__class__.__annotations__.keys())
        for row in self._current_table:
            other_row = other_table_dict.get(getattr(row, join_field_self))
            for field in other_fields:
                if field != join_field_other:
                    new_field = f'{other_table_name}_{field}'
                    other_value = None
                    if other_row:
                        other_value = getattr(other_row, field)
                    setattr(row, new_field, other_value)
