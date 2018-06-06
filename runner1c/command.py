"""
при переопределении декаратор теряется, поэтому нельзя переопределять run
run вызывается, если нужна пред обработка или пост обработка, причем для этого переопределяем execute
execute используется как точка входа в плагин
"""

import abc
import copy
import json
import logging
import os
import subprocess
import tempfile
import time
from enum import Enum

import paramiko

import runner1c.common as common
import runner1c.exit_code


def create_base_if_necessary(func):
    def wrapper(self):
        if getattr(self.arguments, 'connection', False):
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
        self._cmd = []
        self._logger = logging.getLogger(self.name)

        if self._mode == Mode.DESIGNER:
            self._set_designer()
        elif self._mode == Mode.ENTERPRISE:
            self._set_enterprise()
        elif self._mode == Mode.CREATE:
            self._set_create_base()
        else:
            self._add_argument_path_to_1c()

        # noinspection PyPep8
        if not agent_channel is None:
            self._client, self._channel = agent_channel
            self._agent_started = True

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE.error

    @property
    def add_key_for_connection(self):
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

    def start_agent(self):
        if self._agent_started:
            return

        # запуск конфигуратора в режиме агента
        p_agent = runner1c.command.EmptyParameters(self.arguments)
        setattr(p_agent, 'connection', self.arguments.connection)
        setattr(p_agent, 'folder', self.arguments.folder)
        StartAgent(arguments=p_agent).execute()
        time.sleep(1)

        # noinspection PyAttributeOutsideInit
        self._agent_started = True
        self._need_close_agent = True

        # подключение к агенту

        # noinspection PyAttributeOutsideInit
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(hostname='127.0.0.1', username='', password='', port=1543)

        # noinspection PyAttributeOutsideInit
        self._channel = self._client.get_transport().open_session()
        self._channel.invoke_shell()

        # пропуск приветствия
        self._channel.recv(99999)

        # установка формата ответа
        self.send_to_agent('options set --output-format=json --show-prompt=no', False)

        return_code = self.send_to_agent('common connect-ib')
        if not runner1c.exit_code.success_result(return_code):
            raise Exception('Failed connect to agent')

    def send_to_agent(self, command, wait_response=True):
        # noinspection PyPep8
        if not self._agent_started:
            raise Exception('Agent not started')

        result_code = runner1c.exit_code.EXIT_CODE.error
        self.debug('agent send "%s"', command)

        self._channel.send(command + '\n')

        result_sting = self._get_response_from_agent()

        if wait_response:

            response_receive = False

            while not response_receive:

                for line in result_sting.split(']'):
                    if len(line.strip()) == 0:
                        continue

                    try:
                        for element in json.loads(line + ']'):
                            response_type = element.get('type', 'none')
                            if response_type == 'success':
                                result_code = runner1c.exit_code.EXIT_CODE.done
                                response_receive = True
                            elif response_type == 'error':
                                result_code = runner1c.exit_code.EXIT_CODE.error
                                response_receive = True
                    except json.decoder.JSONDecodeError:
                        pass

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
        # noinspection PyPep8
        if not self._agent_started:
            return

        self.send_to_agent('common disconnect-ib', False)
        self.send_to_agent('common shutdown', False)

        self._channel.close()
        self._client.close()

        # noinspection PyAttributeOutsideInit
        self._agent_started = False

        # при старте агента 1с создает файл с настройками клиента, нужно его удалить
        common.delete_file(os.path.join(os.getcwd(), '1cv8u.pfl'))

    def get_agent_channel(self):
        return self._client, self._channel

    def add_argument(self, string):
        self._cmd.append(string)

    def get_string_for_call(self):
        self._set_path_1c()
        self._set_log_result()

        if getattr(self.arguments, 'connection', False):
            self._set_connection_string()

        return ' '.join(self._cmd).format(**vars(self.arguments))

    def _start(self):
        call_string = self.get_string_for_call()
        self.debug('run1C %s', call_string)

        if getattr(self.arguments, 'timeout', 0) > 0:
            result_call = subprocess.call(call_string, timeout=self.arguments.timeout)
        else:
            result_call = subprocess.call(call_string)

        self.debug('result run1C = %s', result_call)

        if os.path.exists(self.arguments.log):
            common.convert_cp1251_to_utf8(self.arguments.log)
            if self.arguments.log.endswith('html'):
                common.save_as_html(self.arguments.log)

        return_code = self._get_result_from_file()
        self.debug('exit code = %s', return_code)

        if not self.arguments.debug:
            self._delete_temp_files()

        return return_code

    def _add_argument_path_to_1c(self):
        self.add_argument('"{path_1c_exe}"')

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
        self._add_argument_path_to_1c()
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
        result = self._channel.recv(99999)

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
        self.debug('parse %s', file_name)

        file_path = os.path.split(file_name)[0]
        module_path = os.path.join(file_path, 'Form')
        if not os.path.exists(module_path):
            os.mkdir(module_path)

        find_string = 0
        open_file = False
        module_file_name = os.path.join(module_path, 'Module.bsl')

        origin_file = open(file_name, mode='rb')

        for line in origin_file:

            if find_string == 1:

                if line.find(b'7fffffff') != -1:
                    find_string = 2

            elif find_string == 2:

                if line.find(b'7fffffff') != -1:
                    break

                line_read = line.decode('utf8')

                line_for_write = ''
                for element in line_read:
                    if ord(element) not in [0, 13, 65279]:
                        line_for_write += element

                if line_for_write != '':
                    if not open_file:
                        module_file = open(module_file_name, mode='w', encoding='utf-8-sig')
                        open_file = True

                    # noinspection PyUnboundLocalVariable
                    module_file.write(line_for_write)

            elif line.find(b'00000024 00000024 7fffffff') != -1:
                find_string = 1

        origin_file.close()

        if open_file:
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

        self.debug('result from file = %s', result_for_compare)
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
        if self.add_key_for_connection:
            if self.arguments.connection.endswith('v8i'):
                type_connection = 'RunShortcut'
            else:
                type_connection = 'IBConnectionString'
            setattr(self.arguments, 'connection_string',
                    '/{} "{}"'.format(type_connection, self.arguments.connection))
        else:
            setattr(self.arguments, 'connection_string', '"{}"'.format(self.arguments.connection))

    def _set_path_1c(self):
        if getattr(self.arguments, 'path', False):
            path = os.path.join(self.arguments.path, 'bin')
        else:
            path = common.get_path_to_max_version_1c()

        file_name_1c = '1cv8.exe'
        if self._mode == Mode.ENTERPRISE and not getattr(self.arguments, 'thick', False):
            file_name_1c = '1cv8c.exe'

        setattr(self.arguments, 'path_1c_exe', os.path.join(path, file_name_1c))

    def _delete_temp_files(self):
        if not self.arguments.external_result:
            common.delete_file(self.arguments.result)

        if not self.arguments.external_log:
            common.delete_file(self.arguments.log)


class Mode(Enum):
    DESIGNER = 'DESIGNER'
    ENTERPRISE = 'ENTERPRISE'
    CREATE = 'CREATEINFOBASE'


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
            setattr(self, 'name', value)


class CreateBase(Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = Mode.CREATE
        super().__init__(**kwargs)

    @property
    def add_key_for_connection(self):
        return False


class StartAgent(Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = Mode.DESIGNER
        super().__init__(**kwargs)
        self.add_argument('/AgentMode /AgentSSHHostKeyAuto /AgentBaseDir "{folder}"')

    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE.done

    def execute(self):
        call_string = self.get_string_for_call()
        return_code = self.default_result

        # noinspection PyPep8,PyBroadException
        try:
            subprocess.Popen('start "no wait" ' + call_string, shell=True)
        except:
            return_code = runner1c.exit_code.EXIT_CODE.error

        return return_code
