import abc


class Parser(abc.ABC):
    def __init__(self, subparsers):
        self._parser = subparsers.add_parser(name=self.name, description=self.description)

    @property
    @abc.abstractmethod
    def name(self):
        pass

    @property
    @abc.abstractmethod
    def description(self):
        pass

    @abc.abstractmethod
    def set_up(self):
        pass

    @abc.abstractmethod
    def create_handler(self, **kwargs):
        pass

    def add_argument_to_parser(self, connection_required=True, authorization=True):
        self._parser.add_argument('--path', help='путь куда установлена платформа 1С '
                                                 '(пример C:\\Program Files (x86)\\1cv8\\8.3.12.1714)')
        self._parser.add_argument('--connection', required=connection_required,
                                  help='строка соединения с информационной базой')
        self._parser.add_argument('--log', help='путь к файлу лога')
        self._parser.add_argument('--result', help='путь к файлу результата')
        self._parser.add_argument('--silent', action='store_const', const=True, help='делает исполнение пакетной '
                                                                                     'команды невидимым пользователю')

        if authorization:
            self._parser.add_argument('--access', help='код доступа к заблокированной базе')
            self._parser.add_argument('--login', help='имя пользователя')
            self._parser.add_argument('--password', help='пароль пользователя')
