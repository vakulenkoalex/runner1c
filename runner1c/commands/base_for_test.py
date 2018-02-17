import runner1c
import runner1c.commands.load_config
import runner1c.commands.start
import runner1c.commands.sync
import runner1c.common as common
import runner1c.exit_code


class CreateBaseForTestParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'base_for_test'

    @property
    def description(self):
        return 'создание базы из исходников для тестирования'

    # noinspection PyMethodMayBeStatic
    def execute(self, **kwargs):
        return CreateBaseForTest(**kwargs).execute()

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--thick', action='store_const', const=True, help='толстый клиент')
        self._parser.add_argument('--folder', required=True, help='путь к папке с репозитарием')
        self._parser.add_argument('--create_epf', action='store_const', const=True, help='создать внешние '
                                                                                         'обработки репозитария')


class CreateBaseForTest(runner1c.command.Command):
    def execute(self):
        folder_for_config_src = 'cf'

        p_create = runner1c.command.EmptyParameters(self.arguments)
        setattr(p_create, 'connection', self.arguments.connection)
        runner1c.command.CreateBase(arguments=p_create).execute()

        self.start_agent()

        try:
            command = 'config load-files --dir "{}\\{}" --update-config-dump-info'
            return_code = self.send_to_agent(command.format(self.arguments.folder, folder_for_config_src))
            if not runner1c.exit_code.success_result(return_code):
                raise Exception('Failed load config')

            return_code = self.send_to_agent('config update-db-cfg')
            if not runner1c.exit_code.success_result(return_code):
                raise Exception('Failed update db')

            # после создания базы можно паралельно создавать обработки и обновлять базу в режиме Предприятия

            if getattr(self.arguments, 'create_epf', False):
                p_sync = runner1c.command.EmptyParameters(self.arguments)
                setattr(p_sync, 'connection', self.arguments.connection)
                setattr(p_sync, 'folder', self.arguments.folder)
                setattr(p_sync, 'create', True)
                runner1c.commands.sync.Sync(arguments=p_sync, agent_channel=self.get_agent_channel()).execute()

        finally:
            self.close_agent()

        p_start = runner1c.command.EmptyParameters(self.arguments)
        setattr(p_start, 'connection', self.arguments.connection)
        setattr(p_start, 'thick', self.arguments.thick)
        setattr(p_start, 'epf', common.get_path_to_project('build\\tools\\epf\\CloseAfterUpdate.epf'))
        runner1c.commands.start.Start(arguments=p_start).execute()

        return 0
