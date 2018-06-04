import runner1c


class DumpExtensionsParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'dump_extensions'

    @property
    def description(self):
        return 'выгрузка расширений конфигурации на исходники'

    # noinspection PyMethodMayBeStatic
    def create_handler(self, **kwargs):
        return DumpExtensions(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--folder', required=True, help='каталог, в который будет выгружены расширения')


class DumpExtensions(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.DESIGNER
        super().__init__(**kwargs)

        self.add_argument('/DumpConfigToFiles "{folder}" -AllExtensions')
