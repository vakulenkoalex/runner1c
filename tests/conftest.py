import logging
import os

import pytest

import runner1c


@pytest.fixture()
def set_log_level(caplog):
    caplog.set_level(logging.DEBUG)


@pytest.fixture()
def runner():
    return runner1c.core.main


@pytest.fixture(scope='session')
def base_dir(tmpdir_factory):
    return tmpdir_factory.mktemp('base')


@pytest.fixture()
def repo_folder():
    test_dir = os.path.dirname(__file__)
    return os.path.join(test_dir, 'repo')
