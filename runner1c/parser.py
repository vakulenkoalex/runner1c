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
    def execute(self, parameters):
        pass

    def add_argument_to_parser(self, connection_required=True):
        self._parser.add_argument('--path', help='путь куда установлена платформа 1С')
        self._parser.add_argument('--connection', required=connection_required,
                                  help='строка соединения с информационной базой')
        self._parser.add_argument('--log', help='путь к файлу лога')
        self._parser.add_argument('--result', help='путь к файлу результата')
