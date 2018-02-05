import runner1c
import runner1c.common as common
import runner1c.scenario


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

            string = common.get_path_to_1c()
            string.append('ENTERPRISE')
            common.add_common_for_all(string)
            common.add_common_for_enterprise_designer(self._parameters, string)

            if getattr(self._parameters, 'thick', False):
                string.append('/RunModeOrdinaryApplication')

            if getattr(self._parameters, 'test_manager', False):
                string.append('/TestManager')

            if getattr(self._parameters, 'epf', False):
                string.append('/Execute "{epf}"')

            if getattr(self._parameters, 'options', False):
                string.append('/C "{options}"')

            setattr(self._parameters, 'cmd', ' '.join(string))

            return self.start()

        else:
            return runner1c.scenario.run_scenario([self], self._parameters, create_base=True)
