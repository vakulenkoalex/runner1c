import runner1c
import runner1c.common as common
import runner1c.scenario


class CreateEpfParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'create_epf'

    @property
    def description(self):
        return 'создание внешних обработок или отчетов из файлов'

    # noinspection PyMethodMayBeStatic
    def execute(self, parameters):
        return CreateEpf(parameters).execute()

    def set_up(self):
        self.add_argument_to_parser(connection_required=False)
        self._parser.add_argument('--epf', required=True,
                                  help='путь к файлу внешней обработки или отчета, в который будет записан результат')
        self._parser.add_argument('--xml', required=True,
                                  help='путь к корневому файлу выгрузки внешний обработки или отчета в формате XML')


class CreateEpf(runner1c.command.Command):
    def execute(self):
        if getattr(self._parameters, 'connection', False):

            string = common.designer_string(self._parameters)
            string.append('/LoadExternalDataProcessorOrReportFromFiles "{xml}" "{epf}"')

            setattr(self._parameters, 'cmd', ' '.join(string))

            return self.start()

        else:
            return runner1c.scenario.run_scenario([self], self._parameters, create_base=True)
