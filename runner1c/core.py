import argparse
import inspect
import logging
import os
import sys

import runner1c.common as common
from runner1c.parser import Parser


def _load_plugins(commands, subparsers):
    commands_dir = "commands"
    modules = []
    package_obj = None

    for file_name in os.listdir(common.get_path_to_script(commands_dir)):
        if file_name.endswith(".py"):
            module_name = file_name[: -3]
            if module_name != "__init__":
                full_module_name = 'runner1c.{dir}.{module}'.format(dir=commands_dir, module=module_name)
                package_obj = __import__(full_module_name)
                modules.append(module_name)

    commands_obj = getattr(package_obj, commands_dir)
    for module_name in modules:
        module_obj = getattr(commands_obj, module_name)
        for elem in dir(module_obj):
            obj = getattr(module_obj, elem)
            if inspect.isclass(obj) and issubclass(obj, Parser):
                parser = obj(subparsers)
                parser.set_up()
                commands[parser.name] = parser


def _add_common_argument(parser):
    parser.add_argument('--debug', action='store_const', const=True, help='отладка')


def _check_override_methods(command):
    methods = ['run']
    for name in methods:
        class_command = command.__class__
        if class_command.__dict__.get(name, None) is not None:
            raise Exception('{} override method {}'.format(class_command.__name__, name))


def main(arg=None):
    commands = {}

    parser = argparse.ArgumentParser()
    _add_common_argument(parser)

    subparsers = parser.add_subparsers(dest='command', description='команда')
    subparsers.required = True
    _load_plugins(commands, subparsers)

    if arg is None:
        list_argument = sys.argv[1:]
        logger_name = 'Core'
    else:
        list_argument = arg
        logger_name = 'File'

    arguments = parser.parse_args(list_argument)

    if arguments.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)19s - %(message)s')

    logger = logging.getLogger(logger_name)
    logger.debug('start')

    handler = commands[arguments.command].create_handler(arguments=arguments)
    _check_override_methods(handler)
    return_code = handler.execute()

    logger.debug('exit code = %s', return_code)

    return return_code


if __name__ == '__main__':
    sys.exit(main())
