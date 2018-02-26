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
    def create_handler(self, **kwargs):
        return File(**kwargs)

    def set_up(self):
        self._parser.add_argument('--params', required=True, help='файл с параметрами')


class File(runner1c.command.Command):
    def run(self):
        params_file = open(self.arguments.params, mode='r+b')
        byte_string = params_file.read(-1)
        params_file.close()

        try:
            string = byte_string.decode('utf8')
        except UnicodeDecodeError:
            string = byte_string.decode('cp1251')

        return runner1c.core.main(string=json.loads(string))
