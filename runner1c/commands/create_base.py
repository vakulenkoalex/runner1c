import runner1c
import runner1c.common as common


class CreateBaseParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'create_base'

    @property
    def description(self):
        return 'создание информационной базы'

    # noinspection PyMethodMayBeStatic
    def execute(self, parameters):
        return CreateBase(parameters).execute()

    def set_up(self):
        self.add_argument_to_parser()


class CreateBase(runner1c.command.Command):
    @property
    def add_key_for_connection(self):
        return False

    def execute(self):
        string = common.get_path_to_1c()
        string.append('CREATEINFOBASE')
        common.add_common_for_all(string)
        common.add_result(string)

        setattr(self._parameters, 'cmd', ' '.join(string))
        return self.start()
