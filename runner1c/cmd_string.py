import copy


class CmdString:
    def __init__(self, parameters):
        self._parameters = copy.copy(parameters)
        self._cmd = []

    def set_designer(self):
        self.add_path_to_1c()
        self.add_string('DESIGNER')
        self._add_for_all_mode()
        self._add_for_enterprise_designer()
        self._add_result()

        if not getattr(self._parameters, 'silent', False):
            self.add_string('/Visible')

    def set_enterprise(self):
        self.add_path_to_1c()
        self.add_string('ENTERPRISE')
        self._add_for_all_mode()
        self._add_for_enterprise_designer()

    def set_create_base(self):
        self.add_path_to_1c()
        self.add_string('CREATEINFOBASE')
        self._add_for_all_mode()
        self._add_result()

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

    def _add_for_all_mode(self):
        self.add_string('{connection_string}')
        self.add_string('/Out "{log}"')
        self.add_string('/L ru')
