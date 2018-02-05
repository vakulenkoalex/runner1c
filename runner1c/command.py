import abc
import copy
import logging
import os
import subprocess
import tempfile

import runner1c.common as common


class Command(abc.ABC):
    def __init__(self, parameters):
        self._parameters = copy.copy(parameters)

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def default_result(self):
        return common.EXIT_CODE['problem']

    @property
    def add_key_for_connection(self):
        return True

    @abc.abstractmethod
    def execute(self):
        pass

    def start(self):
        self._set_path_1c()
        self._set_log_result()

        if getattr(self._parameters, 'connection', False):
            self._set_connection()

        call_string = self._parameters.cmd.format(**vars(self._parameters))

        logging.debug('%s run = %s', self.name, call_string)
        result_call = subprocess.call(call_string)
        logging.debug('%s result_call = %s', self.name, result_call)

        if self._parameters.log.endswith('html'):
            common.save_as_html(self._parameters.log)

        return_code = self._get_result_from_file()
        logging.debug('%s exit_code = %s', self.name, return_code)

        if not self._parameters.debug:
            self._delete_temp_files()

        return return_code

    def _get_result_from_file(self):
        result_code = self.default_result
        result_for_compare = None

        if os.path.exists(self._parameters.result):

            result_stream = open(self._parameters.result, mode='r', encoding='utf-8')
            line = result_stream.readline()
            result_stream.close()

            result_for_compare = common.delete_non_digit_element(line)
            if result_for_compare == '0':
                result_code = common.EXIT_CODE['done']
            elif result_for_compare == '101':
                result_code = common.EXIT_CODE['done']
            elif result_for_compare == '1':
                result_code = common.EXIT_CODE['error']

        logging.debug('%s result_file = %s', self.name, result_for_compare)
        return result_code

    def _set_log_result(self):
        if getattr(self._parameters, 'log', False) and getattr(self._parameters, 'external_log', True):
            setattr(self._parameters, 'external_log', True)
        else:
            setattr(self._parameters, 'log', tempfile.mktemp('.txt'))
            setattr(self._parameters, 'external_log', False)

        if getattr(self._parameters, 'result', False) and getattr(self._parameters, 'external_result', True):
            setattr(self._parameters, 'external_result', True)
        else:
            setattr(self._parameters, 'result', tempfile.mktemp('.txt'))
            setattr(self._parameters, 'external_result', False)

    def _set_connection(self):
        if self.add_key_for_connection:
            if self._parameters.connection.endswith('v8i'):
                type_connection = 'RunShortcut'
            else:
                type_connection = 'IBConnectionString'
            setattr(self._parameters, 'connection_string',
                    '/{} "{}"'.format(type_connection, self._parameters.connection))
        else:
            setattr(self._parameters, 'connection_string', '"{}"'.format(self._parameters.connection))

    def _set_path_1c(self):
        if getattr(self._parameters, 'path', False):
            path = '{}\\bin\\{}'.format(self._parameters.path, '1cv8.exe')
        else:
            path = common.get_path_to_max_version_1c()

        setattr(self._parameters, 'path_1c_exe', path)

    def _delete_temp_files(self):
        if not self._parameters.external_result:
            common.delete_file(self._parameters.result)

        if not self._parameters.external_log:
            common.delete_file(self._parameters.log)


class EmptyParameters:
    def __init__(self, parameters):
        self.debug = parameters.debug

        self.copy_parameter(parameters, 'path')
        self.copy_parameter(parameters, 'log')
        self.copy_parameter(parameters, 'result')

    def copy_parameter(self, parameters, name):
        value = getattr(parameters, name, False)
        if value:
            setattr(self, 'name', value)
