import os

import pytest


@pytest.mark.usefixtures("set_log_level")
def test_sync_without_base(runner):
    test_dir = os.path.dirname(__file__)
    repo_folder = os.path.join(test_dir, 'repo')

    epf = os.path.join(repo_folder, 'build', 'epf', 'CheckConfig.epf')
    if os.path.exists(epf):
        os.remove(epf)
    # обработки нет
    assert not os.path.exists(epf)

    argument = ['--debug',
                'sync',
                '--folder',
                repo_folder,
                '--create']
    assert runner(argument) == 0

    # обработка создалась
    assert os.path.exists(epf)

