import abc


class Parser(abc.ABC):
    def __init__(self, subparsers):
        self.parser = subparsers.add_parser(name=self.name, description=self.description)

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
