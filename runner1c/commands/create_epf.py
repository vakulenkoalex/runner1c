import runner1c


class CreateEpfParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'create_epf'

    @property
    def description(self):
        return 'создание внешних обработок или отчетов из исходников'

    def create_handler(self, **kwargs):
        return CreateEpf(**kwargs)

    def set_up(self):
        self.add_argument_to_parser(connection_required=False)
        self._parser.add_argument('--epf', required=True,
                                  help='путь к файлу внешней обработки или отчета, в который будет записан результат')
        self._parser.add_argument('--xml', required=True,
                                  help='путь к корневому файлу исходников внешней обработки или отчета')


class CreateEpf(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.DESIGNER
        super().__init__(**kwargs)
        self.add_argument('/LoadExternalDataProcessorOrReportFromFiles "{xml}" "{epf}"')
