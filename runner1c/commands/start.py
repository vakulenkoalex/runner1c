import runner1c
import runner1c.exit_code


class StartParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'start'

    @property
    def description(self):
        return 'запуск системы в режиме "Предприятие"'

    # noinspection PyMethodMayBeStatic
    def create_handler(self, **kwargs):
        return Start(**kwargs)

    def set_up(self):
        self.add_argument_to_parser(connection_required=False)
        self._parser.add_argument('--thick', action='store_const', const=True, help='толстый клиент')
        self._parser.add_argument('--test_manager', action='store_const', const=True, help='менеджер тестирования')
        self._parser.add_argument('--epf', help='путь к обработке запускаемой при старте')
        self._parser.add_argument('--options', help='параметры запуска для передачи в клиент')
        self._parser.add_argument('--no_wait', action='store_const', const=True, help='без ожедания результата')


class Start(runner1c.command.Command):
    @property
    def wait_result(self):
        return not getattr(self.arguments, 'no_wait', False)

    @property
    def builder_cmd(self):
        builder = runner1c.cmd_string.CmdString(mode=runner1c.cmd_string.Mode.ENTERPRISE,
                                                parameters=self.arguments)

        if getattr(self.arguments, 'thick', False):
            builder.add_string('/RunModeOrdinaryApplication')

        if getattr(self.arguments, 'test_manager', False):
            builder.add_string('/TestManager')

        if getattr(self.arguments, 'epf', False):
            builder.add_string('/Execute "{epf}"')

        if getattr(self.arguments, 'options', False):
            builder.add_string('/C "{options}"')

        return builder

    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE.done
