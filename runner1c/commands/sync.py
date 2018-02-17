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
        return 'синхранизация исходников и бинарных файлов (отчеты, обработки, фичи)'

    # noinspection PyMethodMayBeStatic
    def execute(self, **kwargs):
        return Sync(**kwargs).execute()

    def set_up(self):
        self.add_argument_to_parser(connection_required=False)
        self._parser.add_argument('--create', action='store_const', const=True, help='создать бинарники из исходников')
        self._parser.add_argument('--folder', required=True, help='путь к папке с репозитарием')


class Sync(runner1c.command.Command):
    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE['done']

    def execute(self):
        if getattr(self.arguments, 'connection', False):
            # noinspection PyAttributeOutsideInit
            self.files_hash = {}
            result_code = self.default_result
            error_in_loop = False

            if getattr(self.arguments, 'create', True):

                self.start_agent()

                source_map = self._get_source()
                for path_source, path_binary in source_map.items():
                    if path_binary.endswith('.epf'):
                        command = 'config load-ext-files --file="{}" --ext-file="{}"'.format(
                            path_source, path_binary)
                        return_code = self.send_to_agent(command)
                        if not runner1c.exit_code.success_result(return_code):
                            error_in_loop = True
                            break
                    else:
                        common.create_path(os.path.dirname(path_binary))
                        shutil.copy(path_source, path_binary)

                self.close_agent()

            else:

                for path_binary, path_source in self._get_change_binary().items():
                    if path_binary.endswith('.epf'):
                        p_dump_epf = runner1c.command.EmptyParameters(self.arguments)
                        setattr(p_dump_epf, 'connection', self.arguments.connection)
                        setattr(p_dump_epf, 'folder', os.path.dirname(path_source))
                        setattr(p_dump_epf, 'epf', path_binary)
                        return_code = runner1c.commands.dump_epf.DumpEpf(arguments=p_dump_epf).execute()
                        if not runner1c.exit_code.success_result(return_code):
                            error_in_loop = True
                            break
                    else:
                        common.create_path(os.path.dirname(path_source))
                        shutil.copy(path_binary, path_source)

            if error_in_loop:
                result_code = runner1c.exit_code.EXIT_CODE['error']

            if result_code == self.default_result:
                if getattr(self.arguments, 'create', True):
                    # noinspection PyUnboundLocalVariable
                    self._fill_files_hash(source_map.values())
                self._save_file_hash()

            return result_code

        else:
            return self.start_no_base()

    @property
    def _binary_folder(self):
        return 'build'

    @property
    def _feature_binary(self):
        return '.data'

    @property
    def _hash_file_name(self):
        file_name = 'hash.txt'
        return os.path.join(self.arguments.folder, self._binary_folder, file_name)

    def _save_file_hash(self):
        with open(self._hash_file_name, mode='w', encoding='utf-8') as file_stream:
            file_stream.write(json.dumps(self.files_hash))
        file_stream.close()

    def _get_source(self):
        exclude = ['.git', 'cf', 'Forms', 'Templates']
        source_map = {}
        for root, dirs, files in os.walk(self.arguments.folder, topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude]
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
        if os.path.exists(self._hash_file_name):
            with open(self._hash_file_name, mode='r', encoding='utf-8') as file_stream:
                # noinspection PyBroadException,PyPep8
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
        self._fill_files_hash(self._get_binary('.feature'))

        old_hash_file = self._read_hash_from_file()

        for key, value in self.files_hash.items():
            if old_hash_file.get(key) != value:
                change_binary.append(key)

        for file_name in change_binary:
            head, tail = os.path.split(file_name)
            new_tail = tail.replace('.feature', self._feature_binary)
            new_tail = new_tail.replace('.epf', '.xml')
            new_head = head.replace(self._binary_folder + '\\', '')
            source_map[file_name] = os.path.join(new_head, new_tail)

        return source_map


def _is_header_epf(file_name):
    with open(file_name, mode='r', encoding='utf-8-sig') as file:
        text = file.read()
    file.close()

    return 'ExternalDataProcessor' in text


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
