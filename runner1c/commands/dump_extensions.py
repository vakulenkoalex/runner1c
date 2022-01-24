import distutils.dir_util as copy_tree
import tempfile

import runner1c
import runner1c.common as common


class DumpExtensionsParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'dump_extensions'

    @property
    def description(self):
        return 'выгрузка расширений конфигурации на исходники'

    def create_handler(self, **kwargs):
        return DumpExtensions(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--folder', required=True, help='каталог, в который будет выгружены расширения')


class DumpExtensions(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.DESIGNER
        super().__init__(**kwargs)
        self.add_argument('/DumpConfigToFiles "{temp_folder}" -AllExtensions')

    def execute(self):
        temp_folder = tempfile.mkdtemp()
        setattr(self.arguments, 'temp_folder', temp_folder)

        self.debug('temp_folder "%s"', self.arguments.temp_folder)

        return_code = self.run()

        common.clear_folder(self.arguments.folder)
        copy_tree.copy_tree(temp_folder, self.arguments.folder)
        common.clear_folder(temp_folder)

        return return_code
