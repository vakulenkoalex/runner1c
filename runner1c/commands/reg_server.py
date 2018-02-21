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
    def create_handler(self, **kwargs):
        return RegServer(**kwargs)

    def set_up(self):
        pass


class RegServer(runner1c.command.Command):
    @property
    def builder_cmd(self):
        builder = runner1c.cmd_string.CmdString()
        builder.add_string('/RegServer -Auto')

        return builder

    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE.done
