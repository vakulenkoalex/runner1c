import runner1c
import runner1c.common as common


class AgentParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'agent'

    @property
    def description(self):
        return 'запуск конфигуратора в режиме агента'

    # noinspection PyMethodMayBeStatic
    def execute(self, parameters):
        return Agent(parameters).execute()

    def set_up(self):
        self.add_argument_to_parser(authorization=False)
        self._parser.add_argument('--folder', required=True, help='базовый каталог, с которым работает sftp-сервер')


class Agent(runner1c.command.Command):
    @property
    def default_result(self):
        return common.EXIT_CODE['done']

    @property
    def wait_result(self):
        return False

    def execute(self):
        builder = runner1c.cmd_string.CmdString(mode=runner1c.cmd_string.Mode.DESIGNER, parameters=self._parameters)
        builder.add_string('/AgentMode /AgentSSHHostKeyAuto /AgentBaseDir "{folder}"')

        setattr(self._parameters, 'cmd', builder.get_string())

        return self.start()
