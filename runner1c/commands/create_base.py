import runner1c


class CreateBaseParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'create_base'

    @property
    def description(self):
        return 'создание информационной базы'

    def create_handler(self, **kwargs):
        return runner1c.command.CreateBase(**kwargs)

    def set_up(self):
        self.add_argument_to_parser(authorization=False)
