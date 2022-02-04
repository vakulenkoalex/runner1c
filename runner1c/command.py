
"""
при переопределении декоратор теряется, поэтому нельзя переопределять run
run вызывается, если нужна пред обработка или пост обработка, причем для этого переопределяем execute
execute используется как точка входа плагина
"""

import abc
import copy
import logging
import os
import socket
import subprocess
import tempfile
import time
from enum import Enum

import paramiko

import runner1c.common as common
import runner1c.exit_code


def create_base_if_necessary(func):
    def wrapper(self):
        if not self.need_connection or getattr(self.arguments, 'connection', False):
            return func(self)
        else:
            temp_folder = tempfile.mkdtemp()
            connection = 'File={}'.format(temp_folder)

            p_create_base = runner1c.command.EmptyParameters(self.arguments)
            setattr(p_create_base, 'connection', connection)
            return_code = CreateBase(arguments=p_create_base).execute()

            if runner1c.exit_code.success_result(return_code):
                setattr(self.arguments, 'connection', connection)
                return_code = self.execute()

            common.clear_folder(temp_folder)

            return return_code

    return wrapper


class Command(abc.ABC):
    def __init__(self, **kwargs):
        self.arguments = copy.copy(kwargs['arguments'])
        self._mode = kwargs.get('mode', None)
        agent_channel = kwargs.get('agent_channel', None)

        self._need_close_agent = False
        self._agent_started = False
        self._logger = logging.getLogger(self.name)
        self._agent_folder = ''
        self._agent_process = None

        self._program_1c_arguments = []
        self._program_1c = ''
        self._version_1c = ''

        if self._mode == Mode.DESIGNER:
            self._set_designer()
        elif self._mode == Mode.ENTERPRISE:
            self._set_enterprise()
        elif self._mode == Mode.CREATE:
            self._set_create_base()

        if agent_channel is not None:
            self._client, self._channel = agent_channel
            self._agent_started = True

        self._set_path_1c()

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE.error

    @property
    def need_connection(self):
        return True

    def execute(self):
        return self.run()

    @create_base_if_necessary
    def run(self):
        return self._start()

    def get_module_ordinary_form(self, dir_for_scan):
        for folder in dir_for_scan:
            for bin_form in self._find_bin_forms(folder):
                self._parse_module_from_bin(bin_form)

    def debug(self, msg, *args):
        self._logger.debug(msg, *args)

    def error(self, msg, *args):
        self._logger.error(msg, *args)

    def start_agent(self):
        if self._agent_started:
            return

        port_agent = self._get_port_for_agent()
        self._agent_folder = os.path.split(self.arguments.folder)[0]

        # запуск конфигуратора в режиме агента
        p_agent = runner1c.command.EmptyParameters(self.arguments)
        setattr(p_agent, 'connection', self.arguments.connection)
        setattr(p_agent, 'folder', self._agent_folder)
        setattr(p_agent, 'port', port_agent)
        agent = StartAgent(arguments=p_agent)
        return_code = agent.execute()
        if not runner1c.exit_code.success_result(return_code):
            raise Exception('Failed start agent')

        self._agent_process = agent.process
        self._agent_started = True
        self._need_close_agent = True
        del agent

        # подключение к агенту

        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(hostname='127.0.0.1', username='', password='', port=port_agent)

        self._channel = self._client.get_transport().open_session()
        self._channel.invoke_shell()

        # пропуск приветствия
        self._channel.recv(common.MAXIMUM_BYTES_READ)

        # установка формата ответа
        self.send_to_agent('options set --output-format=json --show-prompt=no', False)

        return_code = self.send_to_agent('common connect-ib')
        if not runner1c.exit_code.success_result(return_code):
            raise Exception('Failed connect to agent')

    def send_to_agent(self, command, wait_response=True):
        if not self._agent_started:
            raise Exception('Agent not started')

        result_code = runner1c.exit_code.EXIT_CODE.error
        self.debug('agent send "%s"', command)

        self._channel.send(command + '\n')

        result_sting = self._get_response_from_agent()

        if wait_response:

            response_receive = False

            while not response_receive:

                if result_sting.find('"type": "error"') > 0:
                    result_code = runner1c.exit_code.EXIT_CODE.error
                    response_receive = True
                elif result_sting.find('"type": "success"') > 0:
                    result_code = runner1c.exit_code.EXIT_CODE.done
                    response_receive = True

                if response_receive:
                    break

                result_sting = self._get_response_from_agent()

        else:
            result_code = runner1c.exit_code.EXIT_CODE.done

        self.debug('agent response result = %s', result_code)

        return result_code

    def close_agent(self):
        if not self._need_close_agent:
            return
        if not self._agent_started:
            return

        self.send_to_agent('common disconnect-ib', False)

        if not self.bug_platform('8.3.20'):
            self.send_to_agent('common shutdown', False)

        self._channel.close()
        self._client.close()

        self._agent_started = False

        if self.bug_platform('8.3.20'):
            if self._agent_process != None:
                self._agent_process.kill()

        # при старте агента 1с создает служебные файлы, иногда за собой не убирает
        common.delete_file(os.path.join(self._agent_folder, 'agentbasedir.json'))
        common.clear_folder(os.path.join(self._agent_folder, '0'))
        #common.delete_file(os.path.join(os.getcwd(), '1cv8u.pfl'))

    def get_agent_channel(self):
        return self._client, self._channel

    def add_argument(self, string):
        self._program_1c_arguments.append(string)

    def get_program_arguments(self):
        self._set_log_result()

        if getattr(self.arguments, 'connection', False):
            self._set_connection_string()

        return ' '.join(self._program_1c_arguments).format(**vars(self.arguments))

    def version_1c_greater(self, check_version):

        result = True

        part_check_version = check_version.split('.')
        if len(part_check_version) < 4:
            part_check_version.append('0')

        part_current_version = self._version_1c.split('.')

        for element in range(4):
            if int(part_current_version[element]) < int(part_check_version[element]):
                result = False
                break

        return result

    def get_program(self):
        return self._program_1c

    def bug_platform(self, check_version):
        return self.version_1c_greater(check_version)

    def _start(self):
        call_string = self.get_program() + ' ' + self.get_program_arguments()
        self.debug('run1C %s', call_string)

        timeout = getattr(self.arguments, 'timeout', 0)
        if timeout == 0:
            timeout = None
        result_call = subprocess.call(call_string, timeout=timeout)
        self.debug('result run1C = %s', result_call)

        if os.path.exists(self.arguments.log):
            if not self.version_1c_greater('8.3.18'):
                common.convert_cp1251_to_utf8(self.arguments.log)
            if self.arguments.log.endswith('html'):
                common.save_as_html(self.arguments.log)

        return_code = self._get_result_from_file()
        self.debug('exit code = %s', return_code)

        if not self.arguments.debug:
            self._delete_temp_files()

        return return_code

    def _add_argument_result(self):
        self.add_argument('/DumpResult "{result}"')

    def _add_arguments_for_enterprise_designer(self):
        self.add_argument('/DisableStartupDialogs')
        self.add_argument('/DisableStartupMessages')
        if getattr(self.arguments, 'access', False):
            self.add_argument('/UC "{access}"')
        if getattr(self.arguments, 'login', False):
            self.add_argument('/N "{login}"')
        if getattr(self.arguments, 'password', False):
            self.add_argument('/P "{password}"')

    def _set_mode(self, mode):
        self.add_argument(mode.value)
        self.add_argument('{connection_string}')
        self.add_argument('/Out "{log}"')
        self.add_argument('/L ru')

    def _set_enterprise(self):
        self._set_mode(Mode.ENTERPRISE)
        self._add_arguments_for_enterprise_designer()

    def _set_create_base(self):
        self._set_mode(Mode.CREATE)
        self._add_argument_result()

    def _set_designer(self):
        self._set_mode(Mode.DESIGNER)
        self._add_arguments_for_enterprise_designer()
        self._add_argument_result()
        if not getattr(self.arguments, 'silent', False):
            self.add_argument('/Visible')

    def _get_response_from_agent(self):
        while not self._channel.recv_ready():
            pass
        time.sleep(1)
        result = self._channel.recv(common.MAXIMUM_BYTES_READ)

        response = result.decode()
        self.debug('agent response "%s"', response)

        return response

    def _set_connection(self, connection):
        setattr(self.arguments, 'connection', connection)

    @staticmethod
    def _find_bin_forms(dir_for_scan):
        forms_path = []

        for path_element in os.walk(dir_for_scan):

            files = path_element[2]

            if files and files[0] == 'Form.bin':
                forms_path.append(os.path.join(path_element[0], files[0]))

        return forms_path

    def _parse_module_from_bin(self, file_name):
        # первоначально ищем строку 00000024 00000024 7fffffff
        # потом ищем строку заканчивающуюся 7fffffff
        # на следующей строке начинается код формы
        # код формы заканчивается, когда находим строку с 7fffffff
        # последнюю строку кода не берем, если она пустая, иначе получается лишняя пустая строка

        self.debug('parse %s', file_name)

        file_path = os.path.split(file_name)[0]
        module_path = os.path.join(file_path, 'Form')
        if not os.path.exists(module_path):
            os.mkdir(module_path)

        find_string = 0
        line_for_write = ''
        module_file_name = os.path.join(module_path, 'Module.bsl')

        origin_file = open(file_name, mode='rb')
        module_file = open(module_file_name, mode='w', encoding='utf-8-sig')

        for line in origin_file:

            if find_string == 1:

                if line.find(b'7fffffff') != -1:
                    find_string = 2

            elif find_string == 2:

                if line.find(b'7fffffff') != -1:
                    new_line = line_for_write.replace(chr(10), '')
                    if new_line != '':
                        module_file.write(new_line)
                    break

                if line_for_write != '':
                    module_file.write(line_for_write)

                line_read = line.decode('utf8')

                line_for_write = ''
                for element in line_read:
                    if ord(element) not in [0, 13, 65279]:
                        line_for_write += element

            elif line.find(b'00000024 00000024 7fffffff') != -1:
                find_string = 1

        origin_file.close()
        module_file.close()

    def _get_result_from_file(self):
        result_code = self.default_result
        result_for_compare = None

        if os.path.exists(self.arguments.result):

            result_stream = open(self.arguments.result, mode='r', encoding='utf-8')
            line = result_stream.readline()
            result_stream.close()

            result_for_compare = common.delete_non_digit_element(line)
            if result_for_compare == '0':
                result_code = runner1c.exit_code.EXIT_CODE.done
            elif result_for_compare == '101':
                result_code = runner1c.exit_code.EXIT_CODE.done
            elif result_for_compare == '1':
                result_code = runner1c.exit_code.EXIT_CODE.error

        self.debug('result from a file = %s', result_for_compare)
        return result_code

    def _set_log_result(self):
        if getattr(self.arguments, 'log', False) and getattr(self.arguments, 'external_log', True):
            setattr(self.arguments, 'external_log', True)
        else:
            setattr(self.arguments, 'log', tempfile.mktemp('.txt'))
            setattr(self.arguments, 'external_log', False)

        if getattr(self.arguments, 'result', False) and getattr(self.arguments, 'external_result', True):
            setattr(self.arguments, 'external_result', True)
        else:
            setattr(self.arguments, 'result', tempfile.mktemp('.txt'))
            setattr(self.arguments, 'external_result', False)

    def _set_connection_string(self):
        if isinstance(self, CreateBase):
            setattr(self.arguments, 'connection_string', '"{}"'.format(self.arguments.connection))
        else:
            if self.arguments.connection.endswith('v8i'):
                type_connection = 'RunShortcut'
            else:
                type_connection = 'IBConnectionString'
            setattr(self.arguments, 'connection_string',
                    '/{} "{}"'.format(type_connection, self.arguments.connection))

    def _set_path_1c(self):
        if getattr(self.arguments, 'path', False):
            path = os.path.join(self.arguments.path, 'bin')
        else:
            path = common.get_path_to_max_version_1c()

        if self._mode == Mode.WEBINST:
            file_name_1c = 'webinst.exe'
        elif self._mode == Mode.ENTERPRISE and not getattr(self.arguments, 'thick', False):
            file_name_1c = '1cv8c.exe'
        else:
            file_name_1c = '1cv8.exe'

        self._program_1c = os.path.join(path, file_name_1c)
        self.debug('program_1c %s', self._program_1c)
        if not os.path.isfile(self._program_1c):
            raise Exception('Path to 1cv8.exe not found')

        path_1c_element = self._program_1c.split(os.sep)
        self._version_1c = path_1c_element[-3]

    def _delete_temp_files(self):
        if not self.arguments.external_result:
            common.delete_file(self.arguments.result)

        if not self.arguments.external_log:
            common.delete_file(self.arguments.log)

    def _get_port_for_agent(self):

        port_agent = 1543
        find_port = False

        while port_agent < 1600:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port_agent))
            if result == 0:
                port_agent = port_agent + 1
            else:
                sock.close()
                find_port = True
                break

        if not find_port:
            raise Exception('Port for an agent not found')

        return port_agent


class Mode(Enum):
    DESIGNER = 'DESIGNER'
    ENTERPRISE = 'ENTERPRISE'
    CREATE = 'CREATEINFOBASE'
    WEBINST = 'WEBINST'


class EmptyParameters:
    def __init__(self, arguments):
        self.debug = arguments.debug

        self.copy_parameter(arguments, 'path')
        self.copy_parameter(arguments, 'log')
        self.copy_parameter(arguments, 'result')
        self.copy_parameter(arguments, 'silent')

    def copy_parameter(self, arguments, name):
        value = getattr(arguments, name, False)
        if value:
            setattr(self, name, value)


class CreateBase(Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = Mode.CREATE
        super().__init__(**kwargs)


class StartAgent(Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = Mode.DESIGNER
        super().__init__(**kwargs)
        process = None

        self.add_argument('/AgentMode /AgentSSHHostKeyAuto /AgentBaseDir "{folder}"')
        if getattr(self.arguments, 'port', False):
            self.add_argument('/AgentPort {port}')

    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE.done

    def execute(self):
        return_code = self.default_result

        program_arguments = self.get_program_arguments()
        self.debug('get_program_arguments %s', program_arguments)

        file_parameters = tempfile.mktemp('.txt')
        with open(file_parameters, mode='w', encoding='utf8') as file_parameters_stream:
            file_parameters_stream.write(program_arguments)
        file_parameters_stream.close()

        cmd = self.get_program()
        stdin = '/@ ' + file_parameters
        self.debug('Popen %s %s', cmd, stdin)

        try:
            self.process = subprocess.Popen([cmd, stdin])
        except Exception as exception:
            self.error(exception)
            return_code = runner1c.exit_code.EXIT_CODE.error

        self.debug('exit code = %s', return_code)

        time.sleep(3)
        common.delete_file(file_parameters)

        return return_code
