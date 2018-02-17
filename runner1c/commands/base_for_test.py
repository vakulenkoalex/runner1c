import runner1c
import runner1c.commands.load_config
import runner1c.commands.start
import runner1c.commands.sync as sync
import runner1c.common as common
import runner1c.exit_code as exit_code


class CreateBaseForTestParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'base_for_test'

    @property
    def description(self):
        return 'создание базы из исходников для тестирования'

    # noinspection PyMethodMayBeStatic
    def create_handler(self, **kwargs):
        return CreateBaseForTest(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--thick', action='store_const', const=True, help='толстый клиент')
        self._parser.add_argument('--folder', required=True, help='путь к папке с репозитарием')
        self._parser.add_argument('--create_epf', action='store_const', const=True, help='создать внешние '
                                                                                         'обработки репозитария')


class CreateBaseForTest(runner1c.command.Command):
    def execute(self):
        folder_for_config_src = 'cf'

        # после создания базы можно паралельно создавать обработки и обновлять базу в режиме Предприятия

        p_create = runner1c.command.EmptyParameters(self.arguments)
        setattr(p_create, 'connection', self.arguments.connection)
        return_code = runner1c.command.CreateBase(arguments=p_create).execute()

        if exit_code.success_result(return_code):
            self.start_agent()

            command = 'config load-files --dir "{}\\{}" --update-config-dump-info'
            return_code = self.send_to_agent(command.format(self.arguments.folder, folder_for_config_src))
            if exit_code.success_result(return_code):
                return_code = self.send_to_agent('config update-db-cfg')
                if exit_code.success_result(return_code):
                    if getattr(self.arguments, 'create_epf', False):
                        p_sync = runner1c.command.EmptyParameters(self.arguments)
                        setattr(p_sync, 'connection', self.arguments.connection)
                        setattr(p_sync, 'folder', self.arguments.folder)
                        setattr(p_sync, 'create', True)
                        return_code = sync.Sync(arguments=p_sync, agent_channel=self.get_agent_channel()).execute()

            self.close_agent()

            if exit_code.success_result(return_code):
                p_start = runner1c.command.EmptyParameters(self.arguments)
                setattr(p_start, 'connection', self.arguments.connection)
                setattr(p_start, 'thick', self.arguments.thick)
                setattr(p_start, 'epf', common.get_path_to_project('build\\tools\\epf\\CloseAfterUpdate.epf'))
                return_code = runner1c.commands.start.Start(arguments=p_start).execute()

        return return_code
