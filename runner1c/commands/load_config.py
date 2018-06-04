import runner1c


class LoadConfigParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'load_config'

    @property
    def description(self):
        return 'загрузка конфигурации из исходников'

    # noinspection PyMethodMayBeStatic
    def create_handler(self, **kwargs):
        return LoadConfig(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--folder', required=True, help='каталог, содержащий исходники конфигурации')
        self._parser.add_argument('--update', action='store_const', const=True, help='обновление конфигурации '
                                                                                     'базы данных')


class LoadConfig(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.DESIGNER
        super().__init__(**kwargs)

        self.add_argument('/LoadConfigFromFiles "{folder}"')
        if getattr(self.arguments, 'update', False):
            self.add_argument('/UpdateDBCfg')
