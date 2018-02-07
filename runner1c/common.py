import os
import shutil
import tempfile
from functools import partial
import logging
import time

EXIT_CODE = {'done': 0, 'error': 1, 'problem': -1}

get_path_to_project = partial(os.path.join, os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
get_path_to_script = partial(os.path.join, os.path.abspath(os.path.dirname(__file__)))


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


def create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_module_ordinary_form(dir_for_scan):
    start = time.time()
    for folder in dir_for_scan:
        for bin_form in _find_bin_forms(folder):
            _parse_module_from_bin(bin_form)
    stop = time.time()
    logging.debug('get_module_ordinary_form time = %s', stop - start)


def folder_for_class_1c(name):
    if name == 'BusinessProcess':
        result = 'BusinessProcesses'
    elif name == 'ChartOfCharacteristicTypes':
        result = 'ChartsOfCharacteristicTypes'
    elif name == 'FilterCriterion':
        result = 'FilterCriteria'
    elif name == 'ChartOfAccounts':
        result = 'ChartsOfAccounts'
    elif name == 'ChartOfCalculationTypes':
        result = 'ChartsOfCalculationTypes'
    else:
        result = name + 's'

    return result


def _convert_encoding(old, new):
    new_file = open(new, mode='bw')
    old_file = open(old, mode='br')
    new_file.write(old_file.read().decode('cp1251').encode('utf-8'))


def _find_bin_forms(dir_for_scan):
    forms_path = []

    for path_element in os.walk(dir_for_scan):

        files = path_element[2]

        if files and files[0] == 'Form.bin':
            forms_path.append(os.path.join(path_element[0], files[0]))

    return forms_path


def _parse_module_from_bin(file_name):
    logging.debug('parse %s', file_name)

    file_path = os.path.split(file_name)[0]
    module_path = file_path + '\\Form'
    if not os.path.exists(module_path):
        os.mkdir(module_path)

    find_string = 0
    open_file = False
    module_file_name = module_path + '\\Module.bsl'

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
