import logging
import multiprocessing
import os
from logging.handlers import QueueHandler
from logging.handlers import QueueListener

import runner1c
import runner1c.commands.load_config as load_config
import runner1c.commands.load_extension as load_extension
import runner1c.commands.start as start
import runner1c.commands.sync as sync
import runner1c.common as common
import runner1c.exit_code as exit_code


class _ProcessError(Exception):
    def __init__(self, message, code):
        self._message = message
        self._code = code

    def __str__(self):
        return f'{self._message} result = {self._code}'


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


class BaseForTest(runner1c.command.Command):
    def execute(self):
        fixtures_src = os.path.join('spec', 'fixtures')
        lib_src = 'lib'

        config_path = {'config_src': os.path.join(self.arguments.folder, 'cf'),
                       'lib_src': os.path.join(self.arguments.folder, lib_src),
                       'ext_src': os.path.join(self.arguments.folder, lib_src, 'ext'),
                       'fixtures_src': os.path.join(self.arguments.folder, fixtures_src),
                       'fixtures_epf': os.path.join(self.arguments.folder, 'build', fixtures_src)}

        self.start_agent()
        agent_port = self.get_agent_port()
        stream_handler = logging.StreamHandler()
        if self.arguments.debug:
            stream_handler.setLevel(logging.DEBUG)
        queue = multiprocessing.Queue(-1)
        queue_listener = QueueListener(queue, stream_handler)
        queue_listener.start()

        worker = []
        self.debug('start parent multiprocessing')

        base_args = (self.arguments, config_path, agent_port, queue)
        worker.append(multiprocessing.Process(name='create_base', target=_create_base, args=base_args))

        if getattr(self.arguments, 'create_epf', False):
            test_args = (self.arguments, config_path, queue)
            worker.append(multiprocessing.Process(name='create_test', target=_create_test, args=test_args))

        for proc in worker:
            proc.start()
        for proc in worker:
            proc.join()

        self.debug('stop parent multiprocessing')

        queue_listener.stop()
        if getattr(self.arguments, 'need_close_agent', False):
            self.close_agent()

        # todo нужен анализ результата запуска процессов
        return runner1c.exit_code.EXIT_CODE.done


def _create_test(arguments, config_path, queue):
    p_test = runner1c.command.EmptyParameters(arguments)
    setattr(p_test, 'folder', arguments.folder)
    setattr(p_test, 'create', True)
    setattr(p_test, 'exclude', ','.join([config_path['lib_src'], config_path['fixtures_src']]))
    command = sync.Sync(arguments=p_test, logger_handlers=[QueueHandler(queue)])
    return_code = command.execute()
    if not exit_code.success_result(return_code):
        raise _ProcessError(command.get_logger_name(), return_code)


def _create_base(arguments, config_path, agent_port, queue):
    p_create = runner1c.command.EmptyParameters(arguments)
    setattr(p_create, 'connection', arguments.connection)
    command_create = runner1c.command.CreateBase(arguments=p_create, logger_handlers=[QueueHandler(queue)])
    return_code = command_create.execute()
    if not exit_code.success_result(return_code):
        raise _ProcessError(command_create.get_logger_name(), return_code)

    p_load_config = runner1c.command.EmptyParameters(arguments)
    setattr(p_load_config, 'connection', arguments.connection)
    setattr(p_load_config, 'folder', config_path['config_src'])
    setattr(p_load_config, 'agent', True)
    setattr(p_load_config, 'update', True)
    command_load_cf = load_config.LoadConfig(arguments=p_load_config,
                                             agent_port=agent_port,
                                             logger_handlers=[QueueHandler(queue)])
    command_load_cf.connect_to_agent()
    return_code = command_load_cf.execute()
    if not exit_code.success_result(return_code):
        raise _ProcessError(command_load_cf.get_logger_name(), return_code)

    if getattr(arguments, 'create_cfe', False):
        p_extensions = runner1c.command.EmptyParameters(arguments)
        setattr(p_extensions, 'connection', arguments.connection)
        setattr(p_extensions, 'folder', config_path['ext_src'])
        setattr(p_extensions, 'agent', True)
        setattr(p_extensions, 'update', True)
        command_load_ext = load_extension.LoadExtension(arguments=p_extensions,
                                                        agent_channel=command_load_cf.get_agent_channel(),
                                                        logger_handlers=[QueueHandler(queue)])
        return_code = command_load_ext.execute()
        if not exit_code.success_result(return_code):
            raise _ProcessError(command_load_ext.get_logger_name(), return_code)

    if getattr(arguments, 'create_epf', False):
        p_sync = runner1c.command.EmptyParameters(arguments)
        setattr(p_sync, 'connection', arguments.connection)
        setattr(p_sync, 'folder', arguments.folder)
        setattr(p_sync, 'create', True)
        setattr(p_sync, 'include', config_path['fixtures_src'])
        command_create_epf = sync.Sync(arguments=p_sync,
                                        agent_channel=command_load_cf.get_agent_channel(),
                                        logger_handlers=[QueueHandler(queue)])
        return_code = command_create_epf.execute()
        if not exit_code.success_result(return_code):
            raise _ProcessError(command_create_epf.get_logger_name(), return_code)

    command_load_cf.disconnect_from_agent()
    if getattr(arguments, 'create_epf', False):
        command_load_cf.debug('start child multiprocessing')

        args = (arguments, config_path, queue)
        proc_enterprise = multiprocessing.Process(name='start_enterprise',
                                                  target=_start_enterprise,
                                                  args=args)

        args = (arguments, agent_port, config_path, queue)
        proc_create_epf = multiprocessing.Process(name='create_epf',
                                                  target=_create_epf,
                                                  args=args)

        proc_enterprise.start()
        proc_create_epf.start()
        proc_enterprise.join()
        proc_create_epf.join()

        command_load_cf.debug('stop child multiprocessing')
    else:
        _start_enterprise(arguments, config_path, queue)


def _start_enterprise(arguments, config_path, queue):
    p_start = runner1c.command.EmptyParameters(arguments)
    setattr(p_start, 'connection', arguments.connection)
    setattr(p_start, 'thick', arguments.thick)
    setattr(p_start, 'epf', common.get_path_to_project(os.path.join('runner1c',
                                                                    'build',
                                                                    'tools',
                                                                    'epf',
                                                                    'CloseAfterUpdate.epf')))
    if os.path.exists(config_path['fixtures_epf']):
        setattr(p_start, 'options', config_path['fixtures_epf'])
    command = runner1c.commands.start.Start(arguments=p_start, logger_handlers=[QueueHandler(queue)])
    return_code = command.execute()
    if not exit_code.success_result(return_code):
        raise _ProcessError(command.get_logger_name(), return_code)


def _create_epf(arguments, agent_port, config_path, queue):
    p_sync = runner1c.command.EmptyParameters(arguments)
    setattr(p_sync, 'connection', arguments.connection)
    setattr(p_sync, 'folder', arguments.folder)
    setattr(p_sync, 'create', True)
    setattr(p_sync, 'include', config_path['lib_src'])
    command = sync.Sync(arguments=p_sync, agent_port=agent_port, logger_handlers=[QueueHandler(queue)])
    command.connect_to_agent()
    return_code = command.execute()
    command.disconnect_from_agent()
    if not exit_code.success_result(return_code):
        raise _ProcessError(command.get_logger_name(), return_code)
