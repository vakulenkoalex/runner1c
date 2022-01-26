import os

import runner1c
import runner1c.commands.start
import runner1c.common as common


class DiffMxlParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'diff_mxl'

    @property
    def description(self):
        return 'показать расхождение в mxl файлах'

    def create_handler(self, **kwargs):
        return DiffMxl(**kwargs)

    def set_up(self):
        self._parser.add_argument('--first', required=True, help='путь к списку файлов')
        self._parser.add_argument('--second', required=True, help='путь к списку файлов')
        self._parser.add_argument('--equal_files', help='путь к списку файлов, которые совпали')


class DiffMxl(runner1c.command.Command):
    def execute(self):
        options = 'First={};Second={}'.format(self.arguments.first, self.arguments.second)
        if getattr(self.arguments, 'equal_files', False):
            options = '{};Result={}'.format(options, self.arguments.equal_files)

        p_start = runner1c.command.EmptyParameters(self.arguments)
        setattr(p_start, 'thick', True)
        setattr(p_start, 'epf', common.get_path_to_project(os.path.join('runner1c',
                                                                        'build',
                                                                        'tools',
                                                                        'epf',
                                                                        'FileCompareMxl.epf')))
        setattr(p_start, 'options', options)

        return runner1c.commands.start.Start(arguments=p_start).execute()
