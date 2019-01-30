import asyncio
import os

import runner1c
import runner1c.commands.load_config
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

    # noinspection PyMethodMayBeStatic
    def create_handler(self, **kwargs):
        return BaseForTest(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--thick', action='store_const', const=True, help='толстый клиент')
        self._parser.add_argument('--folder', required=True, help='путь к папке с репозитарием')
        self._parser.add_argument('--create_epf', action='store_const', const=True, help='создать внешние '
                                                                                         'обработки репозитария')


async def start_1c(self, loop):
    p_start = runner1c.command.EmptyParameters(self.arguments)
    setattr(p_start, 'connection', self.arguments.connection)
    setattr(p_start, 'thick', self.arguments.thick)
    setattr(p_start, 'epf', common.get_path_to_project(os.path.join('build', 'tools', 'epf', 'CloseAfterUpdate.epf')))

    path_to_fixtures = os.path.join(self.arguments.folder, 'build', 'spec', 'fixtures')
    if os.path.exists(path_to_fixtures):
        setattr(p_start, 'options', path_to_fixtures)

    call_string = runner1c.commands.start.Start(arguments=p_start).get_string_for_call()
    program, parameters = call_string.split(' ENTERPRISE')
    process = await asyncio.create_subprocess_exec(program.replace('"', ''),
                                                   'ENTERPRISE ' + parameters.replace('"', ''),
                                                   loop=loop)
    await process.wait()


async def create_epf(self):
    p_sync = runner1c.command.EmptyParameters(self.arguments)
    setattr(p_sync, 'connection', self.arguments.connection)
    setattr(p_sync, 'folder', self.arguments.folder)
    setattr(p_sync, 'create', True)
    setattr(p_sync, 'exclude', os.path.join(p_sync.folder, 'spec', 'fixtures'))
    sync.Sync(arguments=p_sync, agent_channel=self.get_agent_channel()).execute()


class BaseForTest(runner1c.command.Command):
    def execute(self):
        folder_for_config_src = 'cf'

        p_create = runner1c.command.EmptyParameters(self.arguments)
        setattr(p_create, 'connection', self.arguments.connection)
        return_code = runner1c.command.CreateBase(arguments=p_create).execute()

        if exit_code.success_result(return_code):

            self.start_agent()

            # noinspection PyPep8,PyBroadException
            try:
                command = 'config load-files --dir "{}" --update-config-dump-info'
                return_code = self.send_to_agent(command.format(os.path.join(self.arguments.folder,
                                                                             folder_for_config_src)))
                if exit_code.success_result(return_code):
                    return_code = self.send_to_agent('config update-db-cfg')

                    if exit_code.success_result(return_code):

                        p_sync = runner1c.command.EmptyParameters(self.arguments)
                        setattr(p_sync, 'connection', self.arguments.connection)
                        setattr(p_sync, 'folder', self.arguments.folder)
                        setattr(p_sync, 'create', True)
                        setattr(p_sync, 'include', os.path.join(p_sync.folder, 'spec', 'fixtures'))
                        return_code = sync.Sync(arguments=p_sync, agent_channel=self.get_agent_channel()).execute()

                        if exit_code.success_result(return_code):
                            loop = asyncio.ProactorEventLoop()
                            asyncio.set_event_loop(loop)

                            tasks = []
                            if getattr(self.arguments, 'create_epf', False):
                                tasks.append(create_epf(self))
                            tasks.append(start_1c(self, loop))

                            loop.run_until_complete(asyncio.wait(tasks))
                            loop.close()

            except Exception as exception:
                self.error(exception)
                return_code = runner1c.exit_code.EXIT_CODE.error
            finally:
                self.close_agent()

        return return_code
