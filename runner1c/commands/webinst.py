import runner1c
import runner1c.exit_code as exit_code


class WebinstParser(runner1c.parser.Parser):
    @property
    def name(self):
        return 'webinst'

    @property
    def description(self):
        return 'публикация базы на веб-сервере'

    def create_handler(self, **kwargs):
        return Webinst(**kwargs)

    def set_up(self):
        self.add_argument_to_parser(authorization=False)
        self._parser.add_argument('--wsdir', required=True, help='виртуальный каталог')
        self._parser.add_argument('--dir', required=True, help='физический каталог')
        self._parser.add_argument('--confpath', required=True, help='путь к файлу httpd.conf')


class Webinst(runner1c.command.Command):
    def __init__(self, **kwargs):
        kwargs['mode'] = runner1c.command.Mode.WEBINST
        super().__init__(**kwargs)

        self.add_argument('-publish -apache22 -wsdir {wsdir} -dir {dir} -connstr {connection} -confpath {confpath}')

    @property
    def default_result(self):
        return exit_code.EXIT_CODE.done
