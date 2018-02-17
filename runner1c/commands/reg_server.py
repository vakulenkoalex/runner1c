import runner1c
import runner1c.exit_code


class CreateBaseParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'reg_server'

    @property
    def description(self):
        return 'регистрация "Предприятия" в качестве OLE-Automation-сервера'

    # noinspection PyMethodMayBeStatic
    def execute(self, **kwargs):
        return RegServer(**kwargs).execute()

    def set_up(self):
        pass


class RegServer(runner1c.command.Command):
    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE['done']

    def execute(self):
        builder = runner1c.cmd_string.CmdString()
        builder.add_string('/RegServer -Auto')

        setattr(self.arguments, 'cmd', builder.get_string())
        return self.start()
