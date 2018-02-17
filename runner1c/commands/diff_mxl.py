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

    # noinspection PyMethodMayBeStatic
    def create_handler(self, **kwargs):
        return DiffMxl(**kwargs)

    def set_up(self):
        self._parser.add_argument('--first', required=True, help='путь к первому файлу')
        self._parser.add_argument('--second', required=True, help='путь ко второму файлу')


class DiffMxl(runner1c.command.Command):
    def execute(self):
        p_start = runner1c.command.EmptyParameters(self.arguments)
        setattr(p_start, 'thick', True)
        setattr(p_start, 'epf', common.get_path_to_project('build\\tools\\epf\\FileCompareMxl.epf'))
        setattr(p_start, 'options', 'First={};Second={}'.format(self.arguments.first, self.arguments.second))

        return runner1c.commands.start.Start(arguments=p_start).execute()
