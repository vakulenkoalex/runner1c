import subprocess

import pytest

import runner1c


def capture(command):
    proc = subprocess.Popen(command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            )
    out, err = proc.communicate()
    return out, err, proc.returncode


@pytest.mark.usefixtures("set_log_level")
def test_version_main(capsys, runner):
    argument = ['--debug', 'version']
    assert runner(argument) == 0

    captured = capsys.readouterr()
    assert captured.out == str(runner1c.__version__) + '\n'


def test_version_cli():
    command = ["runner1c", "version"]
    out, err, exitcode = capture(command)
    assert exitcode == 0
    assert out.decode() == str(runner1c.__version__) + '\r\n'
