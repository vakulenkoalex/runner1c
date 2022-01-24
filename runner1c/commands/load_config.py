import runner1c
import runner1c.exit_code as exit_code


class LoadConfigParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'load_config'

    @property
    def description(self):
        return 'загрузка конфигурации из исходников'

    def create_handler(self, **kwargs):
        return LoadConfig(**kwargs)

    def set_up(self):
        self.add_argument_to_parser()
        self._parser.add_argument('--folder', required=True, help='каталог, содержащий исходники конфигурации')
        self._parser.add_argument('--update', action='store_const', const=True, help='обновление конфигурации '
                                                                                     'базы данных')
        self._parser.add_argument('--agent',
                                  action='store_const',
                                  const=True,
                                  help='запускать конфигуратор в режиме агента')


class LoadConfig(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.DESIGNER
        super().__init__(**kwargs)

        if getattr(self.arguments, 'agent', False):
            return

        self.add_argument('/LoadConfigFromFiles "{folder}"')
        if getattr(self.arguments, 'update', False):
            self.add_argument('/UpdateDBCfg')

    def execute(self):
        if not getattr(self.arguments, 'agent', False):
            return self.run()

        self.start_agent()

        try:
            command = 'config load-config-from-files --dir "{}" --update-config-dump-info'
            return_code = self.send_to_agent(command.format(self.arguments.folder))
            if exit_code.success_result(return_code):
                return_code = self.send_to_agent('config update-db-cfg')

        except Exception as exception:
            self.error(exception)
            return_code = exit_code.EXIT_CODE.error
        finally:
            self.close_agent()

        return return_code




