import runner1c


class Version(runner1c.parser.Parser):
    @property
    def name(self):
        return 'version'

    @property
    def description(self):
        return 'версия программы'

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def execute(self, parameters):
        print(runner1c.__version__)
        return 0

    def set_up(self):
        pass
