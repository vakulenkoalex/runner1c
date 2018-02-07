import distutils.dir_util as copy_tree
import glob
import logging
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
    def execute(self, parameters):
        return DumpEpf(parameters).execute()

    def set_up(self):
        self.add_argument_to_parser(connection_required=False)
        self._parser.add_argument('--epf', required=True,
                                  help='путь к файлу внешней обработки или отчета, в который будет записан результат')
        self._parser.add_argument('--folder', required=True,
                                  help='путь к выгрузки, в который будут сохранены файлы в формате XML внешней '
                                       'обработки или отчета')


class DumpEpf(runner1c.command.Command):
    def execute(self):
        if getattr(self._parameters, 'connection', False):

            temp_folder = tempfile.mkdtemp()
            temp_epf = tempfile.mktemp('.epf')
            shutil.copy(self._parameters.epf, temp_epf)

            builder = runner1c.cmd_string.CmdString(mode=runner1c.cmd_string.Mode.DESIGNER, parameters=self._parameters)
            builder.add_string('/DumpExternalDataProcessorOrReportToFiles "{temp_folder}" "{temp_epf}" '
                               '-Format Hierarchical')

            setattr(self._parameters, 'temp_folder', temp_folder)
            setattr(self._parameters, 'temp_epf', temp_epf)
            setattr(self._parameters, 'cmd', builder.get_string())

            logging.debug('%s epf = %s', self.name, self._parameters.epf)
            logging.debug('%s folder = %s', self.name, self._parameters.folder)
            logging.debug('%s temp_epf = %s', self.name, self._parameters.temp_epf)
            logging.debug('%s temp_folder = %s', self.name, self._parameters.temp_folder)

            return_code = self.start()

            common.clear_folder('{}\\{}'.format(self._parameters.folder, _get_epf_name(temp_folder)))
            common.get_module_ordinary_form(temp_folder)
            copy_tree.copy_tree(temp_folder, self._parameters.folder)
            common.clear_folder(temp_folder)
            common.delete_file(temp_epf)

            return return_code

        else:
            return runner1c.scenario.run_scenario([self], self._parameters, create_base=True)


def _get_epf_name(folder):
    full_path_epf = glob.glob(folder + '\\*.xml')[0]
    file_name = os.path.split(full_path_epf)[1]
    epf_name = os.path.splitext(file_name)[0]
    return epf_name
