import os

import pytest


def count_lines_in_file(file):
    with open(file, mode='r', encoding='utf-8') as file_stream:
        count = len(file_stream.readlines())
    file_stream.close()

    return count


def test_diff_same_mxl(runner, tmpdir, repo_folder):
    first = os.path.join(repo_folder, 'Test.mxl')
    second = first
    result = str(tmpdir.join("result.txt"))
    argument = ['diff_mxl', '--first', first, '--second', second, '--equal_files', result]
    assert runner(argument) == 0

    assert count_lines_in_file(result) == 1
