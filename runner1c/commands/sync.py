import hashlib
import json
import os
import shutil

import runner1c
import runner1c.commands.dump_epf
import runner1c.common as common
import runner1c.exit_code


class SyncParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'sync'

    @property
    def description(self):
        return 'синхронизация исходников и бинарных файлов (отчеты, обработки, фичи)'

    def create_handler(self, **kwargs):
        return Sync(**kwargs)

    def set_up(self):
        self.add_argument_to_parser(connection_required=False)
        self._parser.add_argument('--create', action='store_const', const=True, help='создать бинарники из исходников')
        self._parser.add_argument('--folder', required=True, help='путь к папке репозитория')
        self._parser.add_argument('--include', help='путь к папке, из которой нужно собрать бинарники')
        self._parser.add_argument('--exclude', help='путь к папке, которую нужно пропустить')
        self._parser.add_argument('--hash_file', help='файл с хэшем бинарников для проверки изменений')
        self._parser.add_argument('--clear_hash', action='store_const', const=True,
                                  help='удалить старый файл с хэшем бинарников')


class Sync(runner1c.command.Command):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.files_hash = {}

    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE.done

    @runner1c.command.create_base_if_necessary
    def execute(self):
        result_code = self.default_result
        error_in_loop = False
        source_map = {}

        if getattr(self.arguments, 'create', True):

            self.start_agent()

            try:
                source_map = self._get_source()
                for path_source, path_binary in source_map.items():
                    if path_binary.endswith('.feature'):
                        common.create_path(os.path.dirname(path_binary))
                        shutil.copy(path_source, path_binary)
                    else:
                        command = 'config load-ext-files --file="{}" --ext-file="{}"'.format(
                            path_source, path_binary)
                        return_code = self.send_to_agent(command)
                        if not runner1c.exit_code.success_result(return_code):
                            error_in_loop = True
                            break
            except Exception as exception:
                self.error(exception)
                result_code = runner1c.exit_code.EXIT_CODE.error
            finally:
                self.close_agent()

        else:

            for path_binary, path_source in self._get_change_binary().items():
                if path_binary.endswith('.feature'):
                    common.create_path(os.path.dirname(path_source))
                    shutil.copy(path_binary, path_source)
                else:
                    p_dump_epf = runner1c.command.EmptyParameters(self.arguments)
                    setattr(p_dump_epf, 'connection', self.arguments.connection)
                    setattr(p_dump_epf, 'folder', os.path.dirname(path_source))
                    setattr(p_dump_epf, 'file', path_binary)
                    setattr(p_dump_epf, 'access', self.arguments.access)
                    setattr(p_dump_epf, 'login', self.arguments.login)
                    setattr(p_dump_epf, 'password', self.arguments.password)
                    return_code = runner1c.commands.dump_epf.DumpEpf(arguments=p_dump_epf).execute()
                    if not runner1c.exit_code.success_result(return_code):
                        error_in_loop = True
                        break

        if error_in_loop:
            result_code = runner1c.exit_code.EXIT_CODE.error

        if result_code == self.default_result:
            if getattr(self.arguments, 'create', True):
                self._fill_files_hash(source_map.values())
            self._save_file_hash()

        return result_code

    @property
    def _binary_folder(self):
        return 'build'

    @property
    def _feature_binary(self):
        return '.data'

    @property
    def _hash_file_name(self):
        if getattr(self.arguments, 'hash_file', False):
            result = self.arguments.hash_file
        else:
            file_name = 'hash.txt'
            result = os.path.join(self.arguments.folder, self._binary_folder, file_name)

        return result

    def _save_file_hash(self):
        with open(self._hash_file_name, mode='w', encoding='utf-8') as file_stream:
            file_stream.write(json.dumps(self.files_hash))
        file_stream.close()

    def _get_source(self):
        exclude = ['.git', 'cf', 'Forms', 'Templates']
        source_map = {}

        if getattr(self.arguments, 'include', False):
            folder_for_walk = self.arguments.include
        else:
            folder_for_walk = self.arguments.folder

        exclude_full_path = None
        if getattr(self.arguments, 'exclude', False):
            exclude_full_path = self.arguments.exclude

        for root, dirs, files in os.walk(folder_for_walk, topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude and
                       (True if exclude_full_path is None else os.path.join(root, d) != exclude_full_path)]
            for file in files:

                if not file.endswith('.xml') and not file.endswith(self._feature_binary):
                    continue

                path_source = os.path.join(root, file)
                path_binary = os.path.join(self.arguments.folder,
                                           self._binary_folder,
                                           root.replace(self.arguments.folder + '\\', ''),
                                           file)
                if file.endswith('.xml'):
                    if _is_header_epf(path_source):
                        source_map[path_source] = path_binary.replace('.xml', '.epf')
                    elif _is_header_erf(path_source):
                        source_map[path_source] = path_binary.replace('.xml', '.erf')
                elif file.endswith(self._feature_binary):
                    source_map[path_source] = path_binary.replace(self._feature_binary, '.feature')

        return source_map

    def _fill_files_hash(self, files):
        for file_name in files:
            full_path = os.path.join(self.arguments.folder, self._binary_folder, file_name)
            self.files_hash[full_path] = _get_hash_md5(full_path)

    def _get_binary(self, ext):
        binary = []
        for root, dirs, files in os.walk(os.path.join(self.arguments.folder, self._binary_folder)):
            for file in files:
                if file.endswith(ext):
                    file_name = os.path.join(root, file)
                    binary.append(file_name)
        return binary

    def _read_hash_from_file(self):
        files_hash = {}
        if os.path.exists(self._hash_file_name) and not getattr(self.arguments, 'clear_hash', False):
            with open(self._hash_file_name, mode='r', encoding='utf-8') as file_stream:
                try:
                    files_hash = json.loads(file_stream.read())
                except:
                    pass
            file_stream.close()

        return files_hash

    def _get_change_binary(self):

        change_binary = []
        source_map = {}
        self._fill_files_hash(self._get_binary('.epf'))
        self._fill_files_hash(self._get_binary('.erf'))
        self._fill_files_hash(self._get_binary('.feature'))

        old_hash_file = self._read_hash_from_file()

        for key, value in self.files_hash.items():
            if old_hash_file.get(key) != value:
                change_binary.append(key)

        for file_name in change_binary:
            head, tail = os.path.split(file_name)
            new_head = head.replace(self._binary_folder + '\\', '')

            ext = os.path.splitext(file_name)[1]
            if ext == '.feature':
                new_tail = tail.replace(ext, self._feature_binary)
            else:
                new_tail = tail.replace(ext, '.xml')

            source_map[file_name] = os.path.join(new_head, new_tail)

        return source_map


def _is_header_epf(file_name):
    with open(file_name, mode='r', encoding='utf-8-sig') as file:
        text = file.read()
    file.close()

    return 'ExternalDataProcessor' in text


def _is_header_erf(file_name):
    with open(file_name, mode='r', encoding='utf-8-sig') as file:
        text = file.read()
    file.close()

    return 'ExternalReport' in text


def _get_hash_md5(filename):
    with open(filename, 'rb') as file:
        file_hash = hashlib.md5()
        while True:
            data = file.read(8192)
            if not data:
                break
            file_hash.update(data)
    file.close()

    return file_hash.hexdigest()
