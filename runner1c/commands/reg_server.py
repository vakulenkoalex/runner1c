import runner1c
import runner1c.exit_code


class RegServerParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'reg_server'

    @property
    def description(self):
        return 'регистрация "Предприятия" в качестве OLE-Automation-сервера'

    def create_handler(self, **kwargs):
        return RegServer(**kwargs)

    def set_up(self):
        pass


class RegServer(runner1c.command.Command):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument('/RegServer -Auto')

    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE.done

    @property
    def need_connection(self):
        return False
