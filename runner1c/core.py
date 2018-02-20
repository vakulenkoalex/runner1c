"""
script for start 1C with parameter
"""

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

    for file_name in os.listdir(common.get_path_to_script(commands_dir)):
        if file_name.endswith(".py"):
            module_name = file_name[: -3]
            if module_name != "__init__":
                full_module_name = 'runner1c.{dir}.{module}'.format(dir=commands_dir, module=module_name)
                package_obj = __import__(full_module_name)
                modules.append(module_name)

    # noinspection PyUnboundLocalVariable
    commands_obj = getattr(package_obj, commands_dir)
    for module_name in modules:
        module_obj = getattr(commands_obj, module_name)
        for elem in dir(module_obj):
            obj = getattr(module_obj, elem)
            if inspect.isclass(obj):
                if issubclass(obj, Parser):
                    parser = obj(subparsers)
                    parser.set_up()
                    commands[parser.name] = parser


def _add_common_argument(parser):
    parser.add_argument('--debug', action='store_const', const=True, help='отладка')


# noinspection PyUnusedLocal
def main(string=None, as_module=False):
    commands = {}

    parser = argparse.ArgumentParser()
    _add_common_argument(parser)

    subparsers = parser.add_subparsers(dest='command', description='команда')
    subparsers.required = True
    _load_plugins(commands, subparsers)

    if string is None:
        list_argument = sys.argv[1:]
    else:
        list_argument = string.split(' ')
    arguments = parser.parse_args(list_argument)

    if arguments.debug:
        logging.basicConfig(level=logging.DEBUG)

    handler = commands[arguments.command].create_handler(arguments=arguments)
    return handler.execute()


if __name__ == '__main__':
    sys.exit(main(as_module=True))
