import asyncio
import os
import tempfile

import runner1c
import runner1c.commands.load_config as load_config
import runner1c.commands.load_extension as load_extension
import runner1c.commands.start
import runner1c.commands.sync as sync
import runner1c.common as common
import runner1c.exit_code as exit_code


class BaseForTestParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'base_for_test'

    @property
    def description(self):
        return 'создание базы из исходников для тестирования'

    def create_handler(self, **kwargs):
        return BaseForTest(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--thick', action='store_const', const=True, help='толстый клиент')
        self._parser.add_argument('--folder', required=True, help='путь к папке репозитория')
        self._parser.add_argument('--create_epf', action='store_const', const=True, help='создать внешние '
                                                                                         'обработки репозитория')
        self._parser.add_argument('--create_cfe', action='store_const', const=True, help='загрузить расширения '
                                                                                         'репозитория')


async def start_enterprise(self, loop, path_to_fixtures):
    p_start = runner1c.command.EmptyParameters(self.arguments)
    setattr(p_start, 'connection', self.arguments.connection)
    setattr(p_start, 'thick', self.arguments.thick)
    setattr(p_start, 'epf', common.get_path_to_project(os.path.join('runner1c',
                                                                    'build',
                                                                    'tools',
                                                                    'epf',
                                                                    'CloseAfterUpdate.epf')))

    if os.path.exists(path_to_fixtures):
        setattr(p_start, 'options', path_to_fixtures)
    command_start = runner1c.commands.start.Start(arguments=p_start)

    program_arguments = command_start.get_program_arguments()
    self.debug('get_program_arguments %s', program_arguments)

    file_parameters = tempfile.mktemp('.txt')
    with open(file_parameters, mode='w', encoding='utf8') as file_parameters_stream:
        file_parameters_stream.write(program_arguments)
    file_parameters_stream.close()

    cmd = command_start.get_program()
    stdin = '/@ ' + file_parameters

    self.debug('create_subprocess_exec %s %s', cmd, stdin)
    process = await asyncio.create_subprocess_exec(cmd, stdin, loop=loop)

    await process.wait()

    common.delete_file(file_parameters)


async def start_designer(self, exclude):
    p_sync = runner1c.command.EmptyParameters(self.arguments)
    setattr(p_sync, 'connection', self.arguments.connection)
    setattr(p_sync, 'folder', self.arguments.folder)
    setattr(p_sync, 'create', True)
    setattr(p_sync, 'exclude', exclude)
    sync.Sync(arguments=p_sync, agent_channel=self.get_agent_channel()).execute()


class BaseForTest(runner1c.command.Command):
    def execute(self):

        config_src = os.path.join(self.arguments.folder, 'cf')
        lib_src = 'lib'
        ext_src = os.path.join(self.arguments.folder, lib_src, 'ext')
        fixtures_src = os.path.join('spec', 'fixtures')
        epf_src_before_async = ','.join([os.path.join(self.arguments.folder, fixtures_src),
                                          os.path.join(self.arguments.folder, lib_src)])
        path_to_fixtures = os.path.join(self.arguments.folder, 'build', fixtures_src)

        p_create = runner1c.command.EmptyParameters(self.arguments)
        setattr(p_create, 'connection', self.arguments.connection)
        return_code = runner1c.command.CreateBase(arguments=p_create).execute()

        if exit_code.success_result(return_code):

            self.start_agent()

            try:
                p_load_config = runner1c.command.EmptyParameters(self.arguments)
                setattr(p_load_config, 'connection', self.arguments.connection)
                setattr(p_load_config, 'folder', config_src)
                setattr(p_load_config, 'agent', True)
                setattr(p_load_config, 'update', True)
                return_code = load_config.LoadConfig(arguments=p_load_config,
                                                     agent_channel=self.get_agent_channel()).execute()

                if exit_code.success_result(return_code):

                    if getattr(self.arguments, 'create_cfe', False):
                        p_extensions = runner1c.command.EmptyParameters(self.arguments)
                        setattr(p_extensions, 'connection', self.arguments.connection)
                        setattr(p_extensions, 'folder', ext_src)
                        setattr(p_extensions, 'agent', True)
                        setattr(p_extensions, 'update', True)
                        return_code = load_extension.LoadExtension(arguments=p_extensions,
                                                     agent_channel=self.get_agent_channel()).execute()

                    if getattr(self.arguments, 'create_epf', False):
                        p_sync = runner1c.command.EmptyParameters(self.arguments)
                        setattr(p_sync, 'connection', self.arguments.connection)
                        setattr(p_sync, 'folder', self.arguments.folder)
                        setattr(p_sync, 'create', True)
                        setattr(p_sync, 'include', epf_src_before_async)
                        return_code = sync.Sync(arguments=p_sync, agent_channel=self.get_agent_channel()).execute()

                    if exit_code.success_result(return_code):
                        loop = asyncio.ProactorEventLoop()
                        asyncio.set_event_loop(loop)

                        tasks = []
                        if getattr(self.arguments, 'create_epf', False):
                            tasks.append(start_designer(self, epf_src_before_async))
                        tasks.append(start_enterprise(self, loop, path_to_fixtures))

                        loop.run_until_complete(asyncio.wait(tasks))
                        loop.close()

            except Exception as exception:
                self.error(exception)
                return_code = runner1c.exit_code.EXIT_CODE.error
            finally:
                self.close_agent()

        return return_code
