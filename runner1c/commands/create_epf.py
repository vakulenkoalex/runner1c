import runner1c


class CreateEpfParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'create_epf'

    @property
    def description(self):
        return 'создание внешних обработок или отчетов из исходников'

    # noinspection PyMethodMayBeStatic
    def execute(self, **kwargs):
        return CreateEpf(**kwargs).execute()

    def set_up(self):
        self.add_argument_to_parser(connection_required=False)
        self._parser.add_argument('--epf', required=True,
                                  help='путь к файлу внешней обработки или отчета, в который будет записан результат')
        self._parser.add_argument('--xml', required=True,
                                  help='путь к корневому файлу исходников внешний обработки или отчета')


class CreateEpf(runner1c.command.Command):
    def execute(self):
        if getattr(self.arguments, 'connection', False):

            builder = runner1c.cmd_string.CmdString(mode=runner1c.cmd_string.Mode.DESIGNER, parameters=self.arguments)
            builder.add_string('/LoadExternalDataProcessorOrReportFromFiles "{xml}" "{epf}"')

            setattr(self.arguments, 'cmd', builder.get_string())

            return self.start()

        else:
            return self.start_no_base()
