import runner1c
import runner1c.common as common


class StartParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'start'

    @property
    def description(self):
        return 'запуск системы в режиме "Предприятие"'

    # noinspection PyMethodMayBeStatic
    def execute(self, parameters):
        return Start(parameters).execute()

    def set_up(self):
        self.add_argument_to_parser(connection_required=False)
        self._parser.add_argument('--thick', action='store_const', const=True, help='толстый клиент')
        self._parser.add_argument('--test_manager', action='store_const', const=True, help='менеджер тестирования')
        self._parser.add_argument('--epf', help='путь к обработке запускаемой при старте')
        self._parser.add_argument('--options', help='параметры запуска для передачи в клиент')


class Start(runner1c.command.Command):
    @property
    def default_result(self):
        return common.EXIT_CODE['done']

    def execute(self):
        if getattr(self._parameters, 'connection', False):

            builder = runner1c.cmd_string.CmdString(mode=runner1c.cmd_string.Mode.ENTERPRISE,
                                                    parameters=self._parameters)

            if getattr(self._parameters, 'thick', False):
                builder.add_string('/RunModeOrdinaryApplication')

            if getattr(self._parameters, 'test_manager', False):
                builder.add_string('/TestManager')

            if getattr(self._parameters, 'epf', False):
                builder.add_string('/Execute "{epf}"')

            if getattr(self._parameters, 'options', False):
                builder.add_string('/C "{options}"')

            setattr(self._parameters, 'cmd', builder.get_string())

            return self.start()

        else:
            return runner1c.scenario.run_scenario([self], self._parameters, create_base=True)
