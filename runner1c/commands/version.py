import runner1c


class VersionParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'version'

    @property
    def description(self):
        return 'версия программы'

    def create_handler(self, **kwargs):
        return Version(**kwargs)

    def set_up(self):
        pass


class Version(runner1c.command.Command):
    def execute(self):
        print(runner1c.__version__)
        return 0
