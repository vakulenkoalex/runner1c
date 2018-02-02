"""
script for start 1C with parameter
"""

import argparse
import inspect
import logging
import os
import sys
from functools import partial

from runner1c.parser import Parser


def _load_plugins(commands, subparsers):
    get_path_to_here = partial(os.path.join, os.path.abspath(os.path.dirname(__file__)))
    commands_dir = "commands"
    modules = []

    for file_name in os.listdir(get_path_to_here(commands_dir)):
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


def main(as_module=False):
    commands = {}

    parser = argparse.ArgumentParser()
    _add_common_argument(parser)

    subparsers = parser.add_subparsers(dest='command', description='команда')
    subparsers.required = True
    _load_plugins(commands, subparsers)

    parameters = parser.parse_args(sys.argv[1:])
    setattr(parameters, 'as_module', as_module)

    if parameters.debug:
        logging.basicConfig(level=logging.DEBUG)

    handler = commands[getattr(parameters, 'command')]
    sys.exit(handler.execute(parameters))


if __name__ == '__main__':
    main(as_module=True)
