import runner1c


class AgentParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'start_agent'

    @property
    def description(self):
        return 'запуск конфигуратора в режиме агента'

    def create_handler(self, **kwargs):
        return runner1c.command.StartAgent(**kwargs)

    def set_up(self):
        self.add_argument_to_parser(authorization=False)
        self._parser.add_argument('--folder', required=True, help='базовый каталог, с которым работает sftp-сервер')
        self._parser.add_argument('--port', help='номер порта, который использует агент в режиме ssh-сервера '
                                                 '(по умолчанию - 1543)')
