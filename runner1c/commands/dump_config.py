import tempfile
import logging
import re

import runner1c
import runner1c.common as common


class DumpConfigParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'dump_config'

    @property
    def description(self):
        return 'выгрузка конфигурации в XML-файлы'

    # noinspection PyMethodMayBeStatic
    def execute(self, parameters):
        return DumpConfig(parameters).execute()

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--folder', required=True, help='каталог, в который будет выгружена конфигурация')
        self._parser.add_argument('--update', action='store_const', const=True, help='выгрузка изменений')


class DumpConfig(runner1c.command.Command):
    def execute(self):
        builder = runner1c.cmd_string.CmdString(mode=runner1c.cmd_string.Mode.DESIGNER, parameters=self._parameters)
        builder.add_string('/DumpConfigToFiles "{folder}" -Format Hierarchical')

        if getattr(self._parameters, 'update', False):

            changes = tempfile.mktemp('.txt')
            builder.add_string('-update -force -getChanges {changes}')

            setattr(self._parameters, 'changes', changes)
            logging.debug('%s changes = %s', self.name, changes)

        else:
            common.clear_folder(self._parameters.folder)

        setattr(self._parameters, 'cmd', builder.get_string())
        return_code = self.start()

        folders_for_scan = [self._parameters.folder]
        if getattr(self._parameters, 'update', False):
            # noinspection PyUnboundLocalVariable
            with open(changes, mode='r', encoding='utf-8') as file:
                text = file.read()
            file.close()

            if common.delete_non_digit_element(text) == '':
                folders_for_scan = []
            else:
                forms = re.compile('.*\.Form.*\.Form', re.MULTILINE).findall(text)
                if len(forms) > 0:
                    folders_for_scan = self._get_path_changed_forms(forms)

            # noinspection PyUnboundLocalVariable
            common.delete_file(changes)

        if len(folders_for_scan) > 0:
            common.get_module_ordinary_form(folders_for_scan)

        return return_code

    def _get_path_changed_forms(self, forms):
        folders_for_scan = []
        for line in forms:
            parts = line.split(':')[1].split('.')
            class_name = parts[0]
            object_name = parts[1]
            form_name = parts[3]
            folders_for_scan.append('{}\\{}\\{}\\Forms\\{}'.format(self._parameters.folder,
                                                                   common.folder_for_class_1c(class_name),
                                                                   object_name,
                                                                   form_name))
        return folders_for_scan
