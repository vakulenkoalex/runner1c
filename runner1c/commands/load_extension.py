import os

import runner1c
import runner1c.commands.start
import runner1c.common as common
import runner1c.exit_code as exit_code


class LoadExtensionParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'load_extension'

    @property
    def description(self):
        return 'загрузка расширения из исходников'

    def create_handler(self, **kwargs):
        return LoadExtension(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--folder', required=True, help='каталог, содержащий исходники расширений '
                                                                  'конфигурации')
        self._parser.add_argument('--name', help='имя расширений, которые нужно загрузить через запятую')
        self._parser.add_argument('--update', action='store_const', const=True, help='обновление конфигурации '
                                                                                     'базы данных')
        self._parser.add_argument('--agent',
                                  action='store_const',
                                  const=True,
                                  help='запускать конфигуратор в режиме агента')


class LoadExtension(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.DESIGNER
        super().__init__(**kwargs)

        if getattr(self.arguments, 'agent', False):
            return

        if getattr(self.arguments, 'name', False):
            setattr(self.arguments, 'folder_with_ext', os.path.join(self.arguments.folder, self.arguments.name))
        else:
            setattr(self.arguments, 'folder_with_ext', self.arguments.folder)

        self.add_argument('/LoadConfigFromFiles "{folder_with_ext}"')

        if getattr(self.arguments, 'name', False):
            self.add_argument('-Extension "{name}"')
        else:
            self.add_argument('-AllExtensions')

        if getattr(self.arguments, 'update', False):
            self.add_argument('/UpdateDBCfg')

    @property
    def default_result(self):
        return runner1c.exit_code.EXIT_CODE.done

    def execute(self):
        if getattr(self.arguments, 'name', False):
            extensions_name = self.arguments.name.split(',')
        else:
            extensions_name = self._get_extensions_name()

        if len(extensions_name) == 0:
            return self.default_result

        error_code = runner1c.exit_code.EXIT_CODE.error

        if not getattr(self.arguments, 'agent', False):
            if getattr(self.arguments, 'name', False) and len(extensions_name) > 1:
                error_in_loop = False
                for name in extensions_name:
                    p_extensions = runner1c.command.EmptyParameters(self.arguments)
                    setattr(p_extensions, 'connection', self.arguments.connection)
                    setattr(p_extensions, 'folder', self.arguments.folder)
                    setattr(p_extensions, 'name', name)
                    return_code = LoadExtension(arguments=p_extensions).execute()
                    if not runner1c.exit_code.success_result(return_code):
                        error_in_loop = True
                        break
                if error_in_loop:
                    return error_code
                else:
                    return self.default_result
            else:
                return self.run()

        return_code = error_code
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
                if getattr(self.arguments, 'update', False):
                    command = 'config update-db-cfg --extension {}'
                    return_code = self.send_to_agent(command.format(name))
                    if not exit_code.success_result(return_code):
                        break
        except Exception as exception:
            self.error(exception)
            return_code = error_code
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
