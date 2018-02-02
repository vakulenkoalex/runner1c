import json

import runner1c
import runner1c.core


class FileParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'file'

    @property
    def description(self):
        return 'прочитать параметры командной строки из файла'

    # noinspection PyMethodMayBeStatic
    def execute(self, parameters):
        return File(parameters).execute()

    def set_up(self):
        self.parser.add_argument('--params', required=True, help='файл с параметрами')


class File(runner1c.command.Command):
    def execute(self):
        params_file = open(self._parameters.params, mode='r+b')
        byte_string = params_file.read(-1)
        params_file.close()

        try:
            string = byte_string.decode('utf8')
        except UnicodeDecodeError:
            string = byte_string.decode('cp1251')

        return runner1c.core.main(argument=json.loads(string))
