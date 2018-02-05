import runner1c
import runner1c.commands.start as start
import runner1c.common as common


class DiffMxlParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'diff_mxl'

    @property
    def description(self):
        return 'показать расхождение в mxl файлах'

    # noinspection PyMethodMayBeStatic
    def execute(self, parameters):
        p_start = runner1c.command.EmptyParameters(parameters)
        setattr(p_start, 'thick', True)
        setattr(p_start, 'epf', common.get_path_to_project('bin\\epf\\FileCompareMxl.epf'))
        setattr(p_start, 'options', 'First={};Second={}'.format(parameters.first, parameters.second))

        return start.Start(p_start).execute()

    def set_up(self):
        self._parser.add_argument('--first', required=True, help='путь к первому файлу')
        self._parser.add_argument('--second', required=True, help='путь ко второму файлу')
