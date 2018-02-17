import copy
from enum import Enum


class CmdString:
    def __init__(self, parameters=None, mode=None):
        self._cmd = []
        self.mode = mode

        if parameters is not None:
            self._parameters = copy.copy(parameters)

        if mode == Mode.DESIGNER:
            self._set_designer()
        elif mode == Mode.ENTERPRISE:
            self._set_enterprise()
        elif mode == Mode.CREATE:
            self._set_create_base()
        else:
            self.add_path_to_1c()

    def add_path_to_1c(self):
        self.add_string('"{path_1c_exe}"')

    def get_string(self):
        return ' '.join(self._cmd)

    def add_string(self, string):
        self._cmd.append(string)

    def _add_result(self):
        self.add_string('/DumpResult "{result}"')

    def _add_for_enterprise_designer(self):
        self.add_string('/DisableStartupDialogs')
        self.add_string('/DisableStartupMessages')
        if getattr(self._parameters, 'access', False):
            self.add_string('/UC "{access}"')
        if getattr(self._parameters, 'login', False):
            self.add_string('/N "{login}"')
        if getattr(self._parameters, 'password', False):
            self.add_string('/P "{password}"')

    def _set_mode(self, mode):
        self.add_path_to_1c()
        self.add_string(mode.value)
        self.add_string('{connection_string}')
        self.add_string('/Out "{log}"')
        self.add_string('/L ru')

    def _set_enterprise(self):
        self._set_mode(Mode.ENTERPRISE)
        self._add_for_enterprise_designer()

    def _set_create_base(self):
        self._set_mode(Mode.CREATE)
        self._add_result()

    def _set_designer(self):
        self._set_mode(Mode.DESIGNER)
        self._add_for_enterprise_designer()
        self._add_result()
        if not getattr(self._parameters, 'silent', False):
            self.add_string('/Visible')


class Mode(Enum):
    DESIGNER = 'DESIGNER'
    ENTERPRISE = 'ENTERPRISE'
    CREATE = 'CREATEINFOBASE'
