import runner1c


class LoadConfigParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'load_config'

    @property
    def description(self):
        return 'загрузка конфигурации из файлов'

    # noinspection PyMethodMayBeStatic
    def execute(self, **kwargs):
        return LoadConfig(**kwargs).execute()

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--folder', required=True, help='каталог, содержащий исходники конфигурации')
        self._parser.add_argument('--update', action='store_const', const=True, help='обновление конфигурации '
                                                                                     'базы данных')


class LoadConfig(runner1c.command.Command):
    def execute(self):
        builder = runner1c.cmd_string.CmdString(mode=runner1c.cmd_string.Mode.DESIGNER, parameters=self.arguments)
        builder.add_string('/LoadConfigFromFiles "{folder}"')

        if getattr(self.arguments, 'update', False):
            builder.add_string('/UpdateDBCfg')

        setattr(self.arguments, 'cmd', builder.get_string())
        return self.start()
