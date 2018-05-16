import os
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
    def create_handler(self, **kwargs):
        return DumpConfig(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--folder', required=True, help='каталог, в который будет выгружена конфигурация')
        self._parser.add_argument('--update', action='store_const', const=True, help='выгрузка изменений')


class DumpConfig(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.DESIGNER
        super().__init__(**kwargs)
        self.add_argument('/DumpConfigToFiles "{folder}" -Format Hierarchical')

        if getattr(self.arguments, 'update', False):

            # noinspection PyAttributeOutsideInit
            self._changes = tempfile.mktemp('.txt')
            self.add_argument('-update -force -getChanges {changes}')

            setattr(self.arguments, 'changes', self._changes)
            self.debug('changes "%s"', self._changes)

    def execute(self):
        if not getattr(self.arguments, 'update', False):
            common.clear_folder(self.arguments.folder)

        return_code = self.run()

        folders_for_scan = [self.arguments.folder]
        if getattr(self.arguments, 'update', False):
            # noinspection PyUnboundLocalVariable
            with open(self._changes, mode='r', encoding='utf-8') as file:
                text = file.read()
            file.close()

            forms = re.compile('.*\.Form.*\.Form', re.MULTILINE).findall(text)
            if len(forms) > 0:
                folders_for_scan = self._get_path_changed_forms(forms)

            # noinspection PyUnboundLocalVariable
            common.delete_file(self._changes)

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
            folders_for_scan.append(os.path.join(self.arguments.folder,
                                                 common.folder_for_class_1c(class_name),
                                                 object_name,
                                                 'Forms',
                                                 form_name))
        return folders_for_scan
