import tempfile

import runner1c
import runner1c.commands.create_base
import runner1c.common as common


def run_scenario(steps, parameters=None, create_base=False):
    if create_base:
        temp_folder = tempfile.mkdtemp()
        connection = 'File={}'.format(temp_folder)

        for step in steps:
            step.set_connection(connection)

        p_create_base = runner1c.command.EmptyParameters(parameters)
        setattr(p_create_base, 'connection', connection)
        steps.insert(0, runner1c.commands.create_base.CreateBase(p_create_base))

    result_code = common.EXIT_CODE['problem']
    for step in steps:
        result_code = step.execute()
        if result_code != common.EXIT_CODE['done']:
            break

    if create_base:
        # noinspection PyUnboundLocalVariable
        common.clear_folder(temp_folder)

    return result_code
