import os
from multiprocessing import Process

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


def start_enterprise(arguments, path_to_fixtures):
    p_start = runner1c.command.EmptyParameters(arguments)
    setattr(p_start, 'connection', arguments.connection)
    setattr(p_start, 'thick', arguments.thick)
    setattr(p_start, 'epf', common.get_path_to_project(os.path.join('runner1c',
                                                                    'build',
                                                                    'tools',
                                                                    'epf',
                                                                    'CloseAfterUpdate.epf')))

    if os.path.exists(path_to_fixtures):
        setattr(p_start, 'options', path_to_fixtures)
    return_code = runner1c.commands.start.Start(arguments=p_start).execute()
    if not exit_code.success_result(return_code):
        raise Exception(f'Start return = {return_code}')


def start_designer(arguments, agent_port, exclude_epf):
    p_sync = runner1c.command.EmptyParameters(arguments)
    setattr(p_sync, 'connection', arguments.connection)
    setattr(p_sync, 'folder', arguments.folder)
    setattr(p_sync, 'create', True)
    setattr(p_sync, 'exclude', exclude_epf)
    command = sync.Sync(arguments=p_sync, agent_port=agent_port)
    command.connect_to_agent()
    return_code = command.execute()
    command.disconnect_from_agent()
    if not exit_code.success_result(return_code):
        raise Exception(f'SyncExclude return = {return_code}')


class BaseForTest(runner1c.command.Command):
    def execute(self):

        config_src = os.path.join(self.arguments.folder, 'cf')
        lib_src = 'lib'
        ext_src = os.path.join(self.arguments.folder, lib_src, 'ext')
        fixtures_src = os.path.join('spec', 'fixtures')
        epf_src = ','.join([os.path.join(self.arguments.folder, fixtures_src),
                            os.path.join(self.arguments.folder, lib_src)])
        path_to_fixtures = os.path.join(self.arguments.folder, 'build', fixtures_src)

        p_create = runner1c.command.EmptyParameters(self.arguments)
        setattr(p_create, 'connection', self.arguments.connection)
        return_code = runner1c.command.CreateBase(arguments=p_create).execute()

        if not exit_code.success_result(return_code):
            return return_code

        self.start_agent()
        self.connect_to_agent()

        try:
            p_load_config = runner1c.command.EmptyParameters(self.arguments)
            setattr(p_load_config, 'connection', self.arguments.connection)
            setattr(p_load_config, 'folder', config_src)
            setattr(p_load_config, 'agent', True)
            setattr(p_load_config, 'update', True)
            return_code = load_config.LoadConfig(arguments=p_load_config,
                                                 agent_channel=self.get_agent_channel()).execute()
            if not exit_code.success_result(return_code):
                raise Exception(f'LoadConfig return = {return_code}')

            if getattr(self.arguments, 'create_cfe', False):
                p_extensions = runner1c.command.EmptyParameters(self.arguments)
                setattr(p_extensions, 'connection', self.arguments.connection)
                setattr(p_extensions, 'folder', ext_src)
                setattr(p_extensions, 'agent', True)
                setattr(p_extensions, 'update', True)
                return_code = load_extension.LoadExtension(arguments=p_extensions,
                                                           agent_channel=self.get_agent_channel()).execute()
                if not exit_code.success_result(return_code):
                    raise Exception(f'LoadExtension return = {return_code}')

            if getattr(self.arguments, 'create_epf', False):
                p_sync = runner1c.command.EmptyParameters(self.arguments)
                setattr(p_sync, 'connection', self.arguments.connection)
                setattr(p_sync, 'folder', self.arguments.folder)
                setattr(p_sync, 'create', True)
                setattr(p_sync, 'include', epf_src)
                return_code = sync.Sync(arguments=p_sync, agent_channel=self.get_agent_channel()).execute()
                if not exit_code.success_result(return_code):
                    raise Exception(f'SyncInclude return = {return_code}')

            self.disconnect_from_agent()

            if getattr(self.arguments, 'create_epf', False):
                self.debug('start multiprocessing')

                proc_enterprise = Process(target=start_enterprise,
                                          args=(self.arguments, path_to_fixtures),
                                          daemon=True)

                proc_designer = Process(target=start_designer,
                                        args=(self.arguments, self.get_agent_port(), epf_src),
                                        daemon=True)

                proc_enterprise.start()
                proc_designer.start()
                proc_enterprise.join()
                proc_designer.join()

                self.debug('stop multiprocessing')

            else:
                start_enterprise(self.arguments, path_to_fixtures)

        except Exception as exception:
            self.error(exception)
            return_code = runner1c.exit_code.EXIT_CODE.error
        finally:
            self.close_agent()

        return return_code
