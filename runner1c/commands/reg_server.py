import runner1c
import runner1c.common as common


class CreateBaseParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'reg_server'

    @property
    def description(self):
        return 'регистрация "Предприятия" в качестве OLE-Automation-сервера'

    # noinspection PyMethodMayBeStatic
    def execute(self, parameters):
        return RegServer(parameters).execute()

    def set_up(self):
        pass


class RegServer(runner1c.command.Command):
    @property
    def default_result(self):
        return common.EXIT_CODE['done']

    def execute(self):
        builder = runner1c.cmd_string.CmdString()
        builder.add_string('/RegServer -Auto')

        setattr(self._parameters, 'cmd', builder.get_string())
        return self.start()
