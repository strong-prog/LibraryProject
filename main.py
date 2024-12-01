from database.database import DataBase
from menu.base import Menu, Question, ListOfQuestions, ChooseMenu, QuestionInt
from tables import Book, Author, BookStatus


class SelectBook(Question):
    """
    Класс для выбора книги по названию.
    Проверяет, существует ли книга в базе данных.
    """
    def validate(self):
        """
        Проверка существования книги в базе данных.

        :return: True, если книга найдена, иначе False.
        """
        book = DataBase(Book).filter(name=self.answer)
        if book:
            self.answer = book[0]
            return True
        print('Книга не найдена!')
        return False


class DeleteBook(ListOfQuestions):
    """
    Меню для удаления книги из базы данных.
    """
    menu_items = [
        SelectBook('Введите название книги'),
    ]

    def execute(self):
        """
        Удаление выбранной книги из базы данных.
        """
        book = self.menu_items[0].answer

        try:
            DataBase(Book).delete(book.id)
            print(f'Книга "{book.name}" успешно удалена.')
        except Exception as e:
            print(f"Ошибка при удалении книги: {e}")

        self.repeat()


class AddBook(ListOfQuestions):
    """
    Меню для добавления новой книги в базу данных.
    """
    menu_items = [
        Question('Введите название книги'),
        Question('Введите имя автора'),
        QuestionInt('Введите год издания'),
    ]

    def execute(self):
        """
        Добавление книги в базу данных.
        """
        book_name = self.menu_items[0].answer
        author_name = self.menu_items[1].answer
        year = self.menu_items[2].answer

        author = DataBase(Author).filter(name=author_name)
        if not author:
            author_obj = Author(name=author_name)
            DataBase(Author).add(author_obj)
            author_id = author_obj.id
        else:
            author_id = author[0].id

        # Создаем объект книги и добавляем его в базу
        book = Book(name=book_name, author_id=author_id, year=year, status=BookStatus.AVAILABLE)
        DataBase(Book).add(book)
        print(f'Книга "{book_name}" добавлена.')

        self.repeat()


class ListBooks(ListOfQuestions):
    """
    Меню для отображения списка книг.
    """
    menu_items = []

    @staticmethod
    def print_table(results):
        """
        Вывод списка книг в формате таблицы.

        :param results: Список записей из базы данных.
        """
        if not results:
            print('Ничего не найдено')
        for record in results:
            print(
                f"ID: {record.id}, "
                f"Название: {record.name}, "
                f"Автор: {record.author_name if hasattr(record, 'author_name') else ''}, "
                f"Год: {record.year}, "
                f"Статус: {record.status}"
            )

    def execute(self):
        """
        Отображение всех книг в базе данных.
        """
        table = DataBase(Book)
        table.join(Author)
        self.print_table(table.filter())
        self.repeat()


class FilterBooks(ListBooks):
    """
    Меню для фильтрации книг по различным критериям.
    """
    menu_items = [
        Question('Введите значение'),
    ]

    def execute(self):
        """
        Фильтрация книг по выбранному критерию.
        """
        value = self.menu_items[0].answer
        table = DataBase(Book)
        table.join(Author)
        if self.parent.choice == 1:
            results = table.filter(name=lambda field_value: value in field_value)
        elif self.parent.choice == 2:
            results = table.filter(author_name=lambda field_value: value in field_value)
        elif self.parent.choice == 3:
            results = table.filter(year=int(value))

        self.print_table(results)
        self.repeat()


class FilterBooksByStatus(ListBooks):
    """
    Меню для фильтрации книг по статусу.
    """
    menu_items = []

    def execute(self):
        """
        Фильтрация книг по статусу.
        """
        table = DataBase(Book)
        table.join(Author)
        if self.parent.choice == 1:
            results = table.filter(status=BookStatus.AVAILABLE)
        elif self.parent.choice == 2:
            results = table.filter(status=BookStatus.BORROWED)
        self.print_table(results)
        self.repeat(self.parent.parent)


class ChangeBookStatus(Menu):
    """
    Меню для изменения статуса книги.
    """
    parent = None

    def handle(self, parent: Menu | None = None):
        """
        Изменение статуса выбранной книги.
        """
        if parent:
            self.parent = parent
        book_name = input('Введите точное название книги: ')
        table = DataBase(Book)
        table.join(Author)
        results = table.filter(name=book_name)
        choice = None
        if len(results) > 1:
            choice = input('Найдено больше одной книги, повторить? (Y/N)')
        elif not results:
            choice = input('Не найдено ни одной книги, повторить? (Y/N)')

        if choice:
            if choice.lower() in ('y', 'у'):
                self.handle()
            else:
                parent.handle(parent.parent)

        else:
            choice = input(f'Выберите статус:\n1: {BookStatus.AVAILABLE.value}\n2: {BookStatus.BORROWED.value}\n')
            if choice == '1':
                table.update(results[0].id, status = BookStatus.AVAILABLE)
            elif choice == '2':
                table.update(results[0].id, status = BookStatus.BORROWED)
            else:
                repeat = input('Неверный статус, повторить? (Y/N)')
                if repeat.lower() in ('y', 'у'):
                    self.handle()
                else:
                    parent.handle(parent.parent)

            print('Статус успешно изменен')
            parent.handle(parent.parent)

# Главное меню
main_menu = ChooseMenu(
    'Основное меню',
    menu_items=[
        AddBook('Добавить книгу'),
        DeleteBook('Удалить книгу'),
        ChangeBookStatus('Установить статус книги'),
        ChooseMenu(
            'Показать книги',
            menu_items=[
                FilterBooks('Фильтровать по названию'),
                FilterBooks('Фильтровать по автору'),
                FilterBooks('Фильтровать по году'),
                ChooseMenu(
                    'Фильтровать по статусу',
                    menu_items = [
                        FilterBooksByStatus(BookStatus.AVAILABLE.value),
                        FilterBooksByStatus(BookStatus.BORROWED.value),
                    ]
                ),
                ListBooks('Показать все'),
            ]
        )
    ]
)


if __name__ == "__main__":
    """
    Инициализация базы данных и запуск основного меню.
    """
    DataBase.init_db('database.json')
    main_menu.handle()
