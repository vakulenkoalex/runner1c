import os

import runner1c
import runner1c.commands.start
import runner1c.common as common
import runner1c.exit_code as exit_code


class AddExtensionsParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'add_extensions'

    @property
    def description(self):
        return 'добавление расширений в конфигурацию'

    def create_handler(self, **kwargs):
        return AddExtensions(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--folder', required=True, help='каталог, содержащий исходники расширения '
                                                                  'конфигурации')
        self._parser.add_argument('--name', help='имена расширений через запятую')


class AddExtensions(runner1c.command.Command):
    def execute(self):
        return_code = runner1c.exit_code.EXIT_CODE.error

        if getattr(self.arguments, 'name', False):
            extensions_name = self.arguments.name.split(',')
        else:
            extensions_name = self._get_extensions_name()

        if len(extensions_name) == 0:
            return runner1c.exit_code.EXIT_CODE.done

        self.start_agent()

        try:
            for name in extensions_name:
                command = 'config load-files --dir "{}" --extension {}'
                return_code = self.send_to_agent(command.format(os.path.join(self.arguments.folder, name), name))
                if not exit_code.success_result(return_code):
                    break
                if self.version_1c_greater('8.3.14'):
                    command = 'config extensions properties set --extension {} --safe-mode no --unsafe-action-protection no'
                    return_code = self.send_to_agent(command.format(name))
                    if not exit_code.success_result(return_code):
                        break
                command = 'config update-db-cfg --extension {}'
                return_code = self.send_to_agent(command.format(name))
                if not exit_code.success_result(return_code):
                    break
        except Exception as exception:
            self.error(exception)
            return_code = runner1c.exit_code.EXIT_CODE.error
        finally:
            self.close_agent()

        if not self.version_1c_greater('8.3.14') and exit_code.success_result(return_code):
            p_start = runner1c.command.EmptyParameters(self.arguments)
            setattr(p_start, 'connection', self.arguments.connection)
            setattr(p_start, 'epf', common.get_path_to_project(os.path.join('runner1c',
                                                                            'build',
                                                                            'tools',
                                                                            'epf',
                                                                            'ChangeSafeModeForExtension.epf')))
            return_code = runner1c.commands.start.Start(arguments=p_start).execute()

        return return_code

    def _get_extensions_name(self):
        if os.path.exists(self.arguments.folder):
            result = os.listdir(self.arguments.folder)
        else:
            self.debug('не найден каталог расширений')
            result = []

        return result
