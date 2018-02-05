import os
import shutil
import tempfile
from functools import partial

EXIT_CODE = {'done': 0, 'error': 1, 'problem': -1}
get_path_to_project = partial(os.path.join, os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
get_path_to_script = partial(os.path.join, os.path.abspath(os.path.dirname(__file__)))


def run_scenario(steps):
    result_code = EXIT_CODE['problem']
    for step in steps:
        result_code = step.execute()
        if result_code != EXIT_CODE['done']:
            break

    return result_code


def designer_string(parameters):
    string = get_path_to_1c()
    string.append('DESIGNER')
    add_common_for_all(string)
    add_common_for_enterprise_designer(parameters, string)
    add_result(string)

    if not getattr(parameters, 'silent', False):
        string.append('/Visible')

    return string


def clear_folder(folder_name):
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name, True)


def get_path_to_max_version_1c():
    program_files = os.getenv('PROGRAMFILES(X86)')
    if program_files is None:
        program_files = os.getenv('PROGRAMFILES')
        if program_files is None:
            raise Exception('Path to "Program files" not found')

    path_to_1c = os.path.join(program_files, '1cv8')

    versions = [x for x in os.listdir(path_to_1c) if '8.' in x]
    int_version = {}
    for string_version in versions:
        part1, part2, part3, part4 = string_version.split('.')
        int_version[(int(part1), int(part2), int(part3), int(part4))] = string_version
    max_version = int_version[max(int_version)]

    if max_version is None:
        raise Exception('Not found version dirs')

    result = os.path.join(path_to_1c, max_version, 'bin', '1cv8') + ".exe"

    if not os.path.isfile(result):
        raise Exception('File not found {}'.format(result))

    return result


def save_as_html(file_name):
    new_log_file = tempfile.mktemp('.txt')

    with open(new_log_file, mode='w', encoding='cp1251') as new_log_file_stream, \
            open(file_name, mode='r', encoding='cp1251') as log_file:
        for line in log_file:
            new_log_file_stream.write(line.replace('\n', '<br>\n'))

    log_file.close()
    new_log_file_stream.close()

    _convert_encoding(new_log_file, file_name)


def delete_non_digit_element(line):
    line_for_compare = ''
    for element in line:
        if element.isdigit():
            line_for_compare = line_for_compare + element
    return line_for_compare


def delete_file(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)


def get_path_to_1c():
    return ['"{path_1c_exe}"']


def add_result(string):
    string.append('/DumpResult "{result}"')


def add_common_for_enterprise_designer(parameters, string):
    string.append('/DisableStartupDialogs')
    string.append('/DisableStartupMessages')
    if getattr(parameters, 'access', False):
        string.append('/UC "{access}"')
    if getattr(parameters, 'login', False):
        string.append('/N "{login}"')
    if getattr(parameters, 'password', False):
        string.append('/P "{password}"')

    return string


def add_common_for_all(string):
    string.append('{connection_string}')
    string.append('/Out "{log}"')
    string.append('/L ru')

    return string


def _convert_encoding(old, new):
    new_file = open(new, mode='bw')
    old_file = open(old, mode='br')
    new_file.write(old_file.read().decode('cp1251').encode('utf-8'))
