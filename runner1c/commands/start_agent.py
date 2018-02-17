import runner1c


class AgentParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'start_agent'

    @property
    def description(self):
        return 'запуск конфигуратора в режиме агента'

    # noinspection PyMethodMayBeStatic
    def execute(self, **kwargs):
        return runner1c.command.StartAgent(**kwargs).execute()

    def set_up(self):
        self.add_argument_to_parser(authorization=False)
        self._parser.add_argument('--folder', required=True, help='базовый каталог, с которым работает sftp-сервер')
