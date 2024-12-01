import sys
from typing import Any, List

from database.database import DataBase


class Menu:
    """
    Базовый класс меню. Определяет общие свойства и методы для всех типов меню.
    """
    name: str
    parent = None

    def __init__(self, name: str, *args, **kwargs):
        """
        Инициализация меню.

        :param name: Название меню.
        """
        self.name = name

    def handle(self, *args, **kwargs):
        """
        Метод для обработки логики меню. Должен быть переопределен в дочерних классах.
        """
        raise NotImplementedError()


class Question(Menu):
    """
    Меню, представляющее вопрос с валидацией ответа.
    """
    answer: Any

    def __init__(self, name: str):
        """
        Инициализация вопроса.

        :param name: Текст вопроса.
        """
        super().__init__(name)
        self.answer = None

    def validate(self):
        """
        Проверяет валидность ответа. Должен быть переопределен при необходимости.

        :return: Всегда возвращает True (по умолчанию).
        """
        return True

    def handle(self, parent: Menu | None = None):
        """
        Обрабатывает ввод пользователя и валидацию ответа.

        :param parent: Родительское меню (для возврата).
        """
        if parent:
            self.parent = parent
        while True:
            self.answer = input(f'{self.name}: ')
            if self.validate():
                break

            if input(f'Повторить?: ').lower() not in ('y', 'у'):
                parent.parent.handle()


class ListOfQuestions(Menu):
    """
    Меню, состоящее из списка вопросов.
    """
    menu_items = None # Список вопросов.

    def __init__(self, name: str, menu_items: List[Question] | None = None):
        """
        Инициализация списка вопросов.

        :param name: Название меню.
        :param menu_items: Список вопросов.
        """
        super().__init__(name)
        if menu_items:
            self.menu_items = menu_items

    def execute(self):
        """
        Метод для выполнения логики после обработки всех вопросов.
        Должен быть переопределен в наследниках.
        """
        raise NotImplementedError()

    def repeat(self, parent: Menu | None = None):
        """
        Повторяет выполнение списка вопросов.

        :param parent: Родительское меню (для возврата).
        """
        answer = input('Повторить операцию? (Y/N): ')
        if answer.lower() in ('y', 'у'):
            for item in self.menu_items:
                item.answer = None
            self.handle(self.parent)
        elif parent:
            parent.handle(self.parent.parent)
        else:
            self.parent.handle(self.parent.parent)

    def handle(self, parent: Menu | None = None):
        """
        Обрабатывает список вопросов.

        :param parent: Родительское меню.
        """
        if parent:
            self.parent = parent
        for item in self.menu_items:
            item.handle(self)
        self.execute()


class ChooseMenu(Menu):
    """
    Меню с выбором одного из пунктов.
    """
    menu_items = None
    choice: int = None

    def __init__(self, name: str, menu_items: List[Menu] | None = None):
        """
        Инициализация меню выбора.

        :param name: Название меню.
        :param menu_items: Список пунктов меню.
        """
        super().__init__(name)
        if menu_items:
            self.menu_items = menu_items

    def handle(self, parent: Menu | None = None):
        """
        Обрабатывает выбор пункта меню.

        :param parent: Родительское меню.
        """
        if parent:
            self.parent = parent
        n = 0
        for item in self.menu_items:
            n += 1
            print(f'{n}: {item.name}')

        n += 1
        if parent:
            print(f'{n}: Вернуться на уровень выше')
        else:
            print(f'{n}: Выйти')
        print('')

        while True:
            choice = input("Введите номер операции: ")
            try:
                choice = int(choice)
                if choice < 1 or choice > n:
                    raise ValueError
                break
            except ValueError:
                print(f'Введите число не больше {n}')

        self.choice = choice
        if choice == n:
            if parent:
                parent.handle()
            else:
                DataBase.save_db()
                sys.exit()

        item = self.menu_items[choice-1]
        item.handle(self)


class QuestionInt(Question):
    """
    Вопрос, требующий числового ответа.
    """
    def validate(self) -> bool:
        """
        Проверяет, что ответ является числом.

        :return: True, если ответ валиден, иначе False.
        """
        try:
            self.answer = int(self.answer)
            return True
        except ValueError:
            print('Ошибка! Ведите число!')
            return False
