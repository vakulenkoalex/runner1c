import runner1c
import runner1c.exit_code


class StartParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'start'

    @property
    def description(self):
        return 'запуск системы в режиме "Предприятие"'

    def create_handler(self, **kwargs):
        return Start(**kwargs)

    def set_up(self):
        self.add_argument_to_parser(connection_required=False)
        self._parser.add_argument('--thick', action='store_const', const=True, help='толстый клиент')
        self._parser.add_argument('--test_manager', action='store_const', const=True, help='менеджер тестирования')
        self._parser.add_argument('--epf', help='путь к обработке запускаемой при старте')
        self._parser.add_argument('--options', help='параметры запуска для передачи клиенту')
        self._parser.add_argument('--timeout', type=int, default=0, help='таймаут выполнения операции')


class Start(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.ENTERPRISE
        super().__init__(**kwargs)

        if getattr(self.arguments, 'thick', False):
            self.add_argument('/RunModeOrdinaryApplication')

        if getattr(self.arguments, 'test_manager', False):
            self.add_argument('/TestManager')

        if getattr(self.arguments, 'epf', False):
            self.add_argument('/Execute "{epf}"')

        if getattr(self.arguments, 'options', False):
            self.add_argument('/C "{options}"')

    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE.done
