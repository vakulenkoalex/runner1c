import runner1c


class LoadExtensionParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'load_extension'

    @property
    def description(self):
        return 'загрузка расширения из исходников'

    def create_handler(self, **kwargs):
        return LoadExtension(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--folder', required=True, help='каталог, содержащий исходники расширения '
                                                                  'конфигурации')
        self._parser.add_argument('--name', required=True, help='имя расширения, которые нужно загрузить')
        self._parser.add_argument('--update', action='store_const', const=True, help='обновление расширения '
                                                                                     'конфигурации базы данных')


class LoadExtension(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.DESIGNER
        super().__init__(**kwargs)

        self.add_argument('/LoadConfigFromFiles "{folder}" -Extension {name}')
        if getattr(self.arguments, 'update', False):
            self.add_argument('/UpdateDBCfg')
