import distutils.dir_util as copy_tree
import glob
import os
import shutil
import tempfile

import runner1c
import runner1c.common as common


class DumpEpfParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'dump_epf'

    @property
    def description(self):
        return 'создать исходники внешних обработок или отчетов'

    # noinspection PyMethodMayBeStatic
    def execute(self, **kwargs):
        return DumpEpf(**kwargs).execute()

    def set_up(self):
        self.add_argument_to_parser(connection_required=False)
        self._parser.add_argument('--epf', required=True,
                                  help='путь к файлу внешней обработки или отчета, в который будет записан результат')
        self._parser.add_argument('--folder', required=True,
                                  help='путь к выгрузки, в который будут сохранены исходники внешней '
                                       'обработки или отчета')


class DumpEpf(runner1c.command.Command):
    def execute(self):
        if getattr(self.arguments, 'connection', False):

            temp_folder = tempfile.mkdtemp()
            temp_epf = tempfile.mktemp('.epf')
            shutil.copy(self.arguments.epf, temp_epf)

            builder = runner1c.cmd_string.CmdString(mode=runner1c.cmd_string.Mode.DESIGNER, parameters=self.arguments)
            builder.add_string('/DumpExternalDataProcessorOrReportToFiles "{temp_folder}" "{temp_epf}" '
                               '-Format Hierarchical')

            setattr(self.arguments, 'temp_folder', temp_folder)
            setattr(self.arguments, 'temp_epf', temp_epf)
            setattr(self.arguments, 'cmd', builder.get_string())

            self.debug('epf = %s', self.arguments.epf)
            self.debug('folder = %s', self.arguments.folder)
            self.debug('temp_epf = %s', self.arguments.temp_epf)
            self.debug('temp_folder = %s', self.arguments.temp_folder)

            return_code = self.start()

            common.clear_folder('{}\\{}'.format(self.arguments.folder, _get_epf_name(temp_folder)))
            self.get_module_ordinary_form([temp_folder])
            copy_tree.copy_tree(temp_folder, self.arguments.folder)
            common.clear_folder(temp_folder)
            common.delete_file(temp_epf)

            return return_code

        else:
            return self.start_no_base()


def _get_epf_name(folder):
    full_path_epf = glob.glob(folder + '\\*.xml')[0]
    file_name = os.path.split(full_path_epf)[1]
    epf_name = os.path.splitext(file_name)[0]
    return epf_name
