import distutils.dir_util as copy_tree
import glob
import os
import shutil
import tempfile

import runner1c
import runner1c.common as common
import runner1c.exit_code as exit_code


class DumpEpfParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'dump_epf'

    @property
    def description(self):
        return 'создать исходники внешних обработок или отчетов'

    def create_handler(self, **kwargs):
        return DumpEpf(**kwargs)

    def set_up(self):
        self.add_argument_to_parser(connection_required=False)
        self._parser.add_argument('--file', required=True,
                                  help='путь к файлу внешней обработки или отчета')
        self._parser.add_argument('--folder', required=True,
                                  help='путь, в который будут сохранены исходники внешней обработки или отчета')


class DumpEpf(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.DESIGNER
        super().__init__(**kwargs)
        self.add_argument('/DumpExternalDataProcessorOrReportToFiles "{temp_folder}" "{temp_file}" '
                          '-Format Hierarchical')

    def execute(self):
        if getattr(self.arguments, 'connection', False):
            temp_folder = tempfile.mkdtemp()
            temp_file = tempfile.mktemp(os.path.splitext(self.arguments.file)[1])
            shutil.copy(self.arguments.file, temp_file)

            setattr(self.arguments, 'temp_folder', temp_folder)
            setattr(self.arguments, 'temp_file', temp_file)

            self.debug('file "%s"', self.arguments.file)
            self.debug('temp_file "%s"', self.arguments.temp_file)
            self.debug('temp_folder "%s"', self.arguments.temp_folder)

            return_code = self.run()

            if return_code == exit_code.EXIT_CODE.done:
                common.clear_folder(os.path.join(self.arguments.folder, _get_file_name_from_xml(temp_folder)))
                self.get_module_ordinary_form([temp_folder])
                copy_tree.copy_tree(temp_folder, self.arguments.folder)
                common.clear_folder(temp_folder)
                common.delete_file(temp_file)

            return return_code
        else:
            return self.run()


def _get_file_name_from_xml(folder):
    full_path = glob.glob(folder + '\\*.xml')[0]
    file_name = os.path.split(full_path)[1]
    name = os.path.splitext(file_name)[0]
    return name
