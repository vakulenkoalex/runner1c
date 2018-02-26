import runner1c


class VersionParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'version'

    @property
    def description(self):
        return 'версия программы'

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def create_handler(self, **kwargs):
        return Version()

    def set_up(self):
        pass


class Version(runner1c.command.Command):
    def run(self):
        print(runner1c.__version__)
        return 0
