import os
import shutil
import tempfile

import runner1c


class PlatformCheckParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'platform_check'

    @property
    def description(self):
        return 'проверка конфигурации'

    def create_handler(self, **kwargs):
        return PlatformCheckConfig(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--options', required=True, help='опции проверки как в справке 1с')
        self._parser.add_argument('--skip_error', help='путь к файлу ошибок-исключений')
        self._parser.add_argument('--skip_object', help='путь к файлу с объектами, в которых ошибки игнорируются')
        self._parser.add_argument('--skip_modality', help='путь к файлу с объектами, в которых игнорируются ошибки '
                                                          'модальных вызовов')


class PlatformCheckConfig(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.DESIGNER
        super().__init__(**kwargs)

        self.arguments.options1c = ' '.join(['-' + x for x in self.arguments.options.split(' ')])
        self.add_argument('/CheckConfig {options1c}')

    def execute(self):
        return_code = self.run()

        _delete_plug_function(self.arguments.log)
        if getattr(self.arguments, 'skip_object'):
            _delete_skip_object(self.arguments.skip_object, self.arguments.log)
        _delete_skip_error(self.arguments, self.arguments.log)
        if getattr(self.arguments, 'skip_modality'):
            _delete_modality_error(self.arguments.skip_modality, self.arguments.log)

        return return_code


def _delete_plug_function(log):
    unreference_procedure_error = 'Не обнаружено ссылок на'
    procedure_name_connectable = 'Подключаемый_'
    procedure_name_upload = 'ЗагрузитьИзТабличногоДокумента'

    new_log_file = tempfile.mktemp('.txt')
    new_log_file_stream = open(new_log_file, mode='w', encoding='utf-8')

    log_file = open(log, mode='r', encoding='utf-8')
    for line in log_file:
        if (unreference_procedure_error not in line) or \
                ((procedure_name_connectable not in line) and (procedure_name_upload not in line)):
            new_log_file_stream.write(line)

    log_file.close()
    new_log_file_stream.close()
    shutil.move(new_log_file, log)


def _read_file_to_list(file_name):
    file_stream = open(file_name, mode='r', encoding='utf-8')
    lines = file_stream.readlines()
    file_stream.close()

    return lines


def _delete_modality_error(skip_modality, log):
    if not os.path.exists(skip_modality):
        return

    modality_error = 'Использование модального вызова'

    modality_lines = _read_file_to_list(skip_modality)

    new_log_file = tempfile.mktemp('.txt')
    new_log_file_stream = open(new_log_file, mode='w', encoding='utf-8')

    log_file = open(log, mode='r', encoding='utf-8')
    for line in log_file:
        add_string = True
        if modality_error in line:
            for error_line in modality_lines:
                if error_line.strip() in line:
                    add_string = False
                    break
        if add_string:
            new_log_file_stream.write(line)

    log_file.close()
    new_log_file_stream.close()
    shutil.move(new_log_file, log)


def _delete_skip_object(skip_object, log):
    if not os.path.exists(skip_object):
        return

    skip_objects = _read_file_to_list(skip_object)

    new_log_file = tempfile.mktemp('.txt')
    new_log_file_stream = open(new_log_file, mode='w', encoding='utf-8')

    add_string = True
    log_file = open(log, mode='r', encoding='utf-8')
    for line in log_file:
        if line[0] != '\t':  # если строка начинается с табуляции, значит она относиться к предыдущей строке
            break_exit = False
            for ignore_object in skip_objects:
                if ignore_object.strip() in line:
                    add_string = False
                    break_exit = True
                    break
            if not break_exit:
                add_string = True
        if add_string:
            new_log_file_stream.write(line)

    log_file.close()
    new_log_file_stream.close()
    shutil.move(new_log_file, log)


def _delete_skip_error(arguments, log):
    skip_lines = []
    if getattr(arguments, 'skip_error'):
        skip_lines = _read_file_to_list(arguments.skip_error)
    skip_lines.append('Ошибок не обнаружено\n')

    new_log_file = tempfile.mktemp('.txt')
    new_log_file_stream = open(new_log_file, mode='w', encoding='utf-8')

    log_file = open(log, mode='r', encoding='utf-8')
    for line in log_file:
        add_string = True
        for error_line in skip_lines:
            if error_line.strip() in line:
                add_string = False
                break
        if add_string:
            new_log_file_stream.write(line)

    log_file.close()
    new_log_file_stream.close()
    shutil.move(new_log_file, log)
