import runner1c


class CreateBaseParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'create_base'

    @property
    def description(self):
        return 'создание информационной базы'

    # noinspection PyMethodMayBeStatic
    def execute(self, parameters):
        return CreateBase(parameters).execute()

    def set_up(self):
        self.add_argument_to_parser(authorization=False)


class CreateBase(runner1c.command.Command):
    @property
    def add_key_for_connection(self):
        return False

    def execute(self):
        builder = runner1c.cmd_string.CmdString(mode=runner1c.cmd_string.Mode.CREATE)

        setattr(self._parameters, 'cmd', builder.get_string())
        return self.start()
