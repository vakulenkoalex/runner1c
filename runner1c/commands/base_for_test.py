import runner1c
import runner1c.commands.create_base
import runner1c.commands.load_config
import runner1c.commands.start
import runner1c.commands.sync
import runner1c.common as common


class CreateBaseForTestParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'base_for_test'

    @property
    def description(self):
        return 'создание базы из исходников для тестирования'

    # noinspection PyMethodMayBeStatic
    def execute(self, parameters):
        folder_for_config_src = 'cf'
        steps = []

        p_create = runner1c.command.EmptyParameters(parameters)
        setattr(p_create, 'connection', parameters.connection)
        steps.append(runner1c.commands.create_base.CreateBase(p_create))

        p_load_config = runner1c.command.EmptyParameters(parameters)
        setattr(p_load_config, 'connection', parameters.connection)
        setattr(p_load_config, 'folder', '{}\\{}'.format(parameters.folder, folder_for_config_src))
        setattr(p_load_config, 'update', True)
        steps.append(runner1c.commands.load_config.LoadConfig(p_load_config))

        p_start = runner1c.command.EmptyParameters(parameters)
        setattr(p_start, 'connection', parameters.connection)
        setattr(p_start, 'thick', parameters.thick)
        setattr(p_start, 'epf', common.get_path_to_project('build\\tools\\epf\\CloseAfterUpdate.epf'))
        steps.append(runner1c.commands.start.Start(p_start))

        if getattr(parameters, 'create_epf', False):
            p_sync = runner1c.command.EmptyParameters(parameters)
            setattr(p_sync, 'connection', parameters.connection)
            setattr(p_sync, 'folder', parameters.folder)
            setattr(p_sync, 'create', True)
            steps.append(runner1c.commands.sync.Sync(p_sync))

        return runner1c.scenario.run_scenario(steps)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--thick', action='store_const', const=True, help='толстый клиент')
        self._parser.add_argument('--folder', required=True, help='путь к папке с репозитарием')
        self._parser.add_argument('--create_epf', action='store_const', const=True, help='создать внешние '
                                                                                         'обработки репозитария')
