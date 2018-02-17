import re
import tempfile

import runner1c
import runner1c.common as common


class DumpConfigParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'dump_config'

    @property
    def description(self):
        return 'выгрузка конфигурации на исходники'

    # noinspection PyMethodMayBeStatic
    def execute(self, **kwargs):
        return DumpConfig(**kwargs).execute()

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--folder', required=True, help='каталог, в который будет выгружена конфигурация')
        self._parser.add_argument('--update', action='store_const', const=True, help='выгрузка изменений')


class DumpConfig(runner1c.command.Command):
    def execute(self):
        builder = runner1c.cmd_string.CmdString(mode=runner1c.cmd_string.Mode.DESIGNER, parameters=self.arguments)
        builder.add_string('/DumpConfigToFiles "{folder}" -Format Hierarchical')

        if getattr(self.arguments, 'update', False):

            changes = tempfile.mktemp('.txt')
            builder.add_string('-update -force -getChanges {changes}')

            setattr(self.arguments, 'changes', changes)
            self.debug('changes = %s', changes)

        else:
            common.clear_folder(self.arguments.folder)

        setattr(self.arguments, 'cmd', builder.get_string())
        return_code = self.start()

        folders_for_scan = [self.arguments.folder]
        if getattr(self.arguments, 'update', False):
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
            self.get_module_ordinary_form(folders_for_scan)

        return return_code

    def _get_path_changed_forms(self, forms):
        folders_for_scan = []
        for line in forms:
            parts = line.split(':')[1].split('.')
            class_name = parts[0]
            object_name = parts[1]
            form_name = parts[3]
            folders_for_scan.append('{}\\{}\\{}\\Forms\\{}'.format(self.arguments.folder,
                                                                   common.folder_for_class_1c(class_name),
                                                                   object_name,
                                                                   form_name))
        return folders_for_scan
