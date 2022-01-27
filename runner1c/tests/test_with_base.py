# todo убрать задвоенность в test_platform_check и count_lines_in_file
# todo RunShortcut v8i

import distutils.dir_util as copy_tree
import os.path
import shutil
import xml.etree.ElementTree as ElementTree

import pytest


def options_for_platform_check():
    return 'ConfigLogIntegrity IncorrectReferences ThinClient WebClient Server ExternalConnection ' \
           'ExternalConnectionServer ThickClientOrdinaryApplication ThickClientServerOrdinaryApplication ' \
           'UnreferenceProcedures HandlersExistence EmptyHandlers ExtendedModulesCheck CheckUseModality'


def count_lines_in_file(file):
    with open(file, mode='r', encoding='utf-8') as file_stream:
        count = len(file_stream.readlines())
    file_stream.close()

    return count


@pytest.mark.dependency()
@pytest.mark.usefixtures("set_log_level")
def test_base_for_test(tmpdir, runner, base_dir):
    test_dir = os.path.dirname(__file__)
    repo_folder = os.path.join(test_dir, 'repo')
    epf = os.path.join(repo_folder, 'build', 'epf', 'CheckConfig.epf')
    result = str(tmpdir.join("result.txt"))

    argument = ['--debug',
                'base_for_test',
                '--connection',
                'File={}'.format(base_dir),
                '--folder',
                repo_folder,
                '--create_epf']
    assert runner(argument) == 0

    # обработка создалась
    assert os.path.exists(epf)

    # проверка базы
    argument = ['--debug',
                'start',
                '--connection',
                'File={}'.format(base_dir),
                '--result',
                result,
                '--epf',
                epf,
                '--option',
                result]
    assert runner(argument) == 0


@pytest.mark.dependency(depends=["test_base_for_test"])
@pytest.mark.usefixtures("set_log_level")
def test_sync(tmpdir, runner, repo_folder):
    new_repo = str(tmpdir.join("repo"))
    old_build = os.path.join(repo_folder, 'build')
    new_build = os.path.join(new_repo, 'build')
    copy_tree.copy_tree(old_build, new_build)

    argument = ['--debug',
                'sync',
                '--folder',
                new_repo]
    assert runner(argument) == 0

    assert os.path.exists(os.path.join(repo_folder, 'epf', 'CheckConfig.xml'))
    assert os.path.exists(os.path.join(repo_folder, 'feature', 'Example.data'))


@pytest.mark.dependency(depends=["test_base_for_test"])
@pytest.mark.usefixtures("set_log_level")
def test_platform_check_with_error(tmpdir, runner, base_dir):
    log = str(tmpdir.join("log.html"))
    argument = ['--debug',
                'platform_check',
                '--connection',
                'File={}'.format(base_dir),
                '--log',
                log,
                '--options',
                '"{}"'.format(options_for_platform_check())]
    assert runner(argument) == 0
    assert count_lines_in_file(log) == 1


@pytest.mark.dependency(depends=["test_base_for_test"])
@pytest.mark.usefixtures("set_log_level")
def test_platform_check_skip_modality(tmpdir, runner, base_dir):
    skip_file = str(tmpdir.join("skip.txt"))
    with open(skip_file, mode='w', encoding='utf-8') as file:
        file.write('Справочник.Catalog1.Форма.Form.Форма')
    file.close()

    log = str(tmpdir.join("log.html"))
    argument = ['--debug',
                'platform_check',
                '--connection',
                'File={}'.format(base_dir),
                '--log',
                log,
                '--options',
                '"{}"'.format(options_for_platform_check()),
                '--skip_modality',
                skip_file]
    assert runner(argument) == 0
    assert count_lines_in_file(log) == 0


@pytest.mark.dependency(depends=["test_base_for_test"])
@pytest.mark.usefixtures("set_log_level")
def test_platform_check_skip_object(tmpdir, runner, base_dir):
    skip_file = str(tmpdir.join("skip.txt"))
    with open(skip_file, mode='w', encoding='utf-8') as file:
        file.write('Справочник.Catalog1')
    file.close()

    log = str(tmpdir.join("log.html"))
    argument = ['--debug',
                'platform_check',
                '--connection',
                'File={}'.format(base_dir),
                '--log',
                log,
                '--options',
                '"{}"'.format(options_for_platform_check()),
                '--skip_object',
                skip_file]
    assert runner(argument) == 0
    assert count_lines_in_file(log) == 0


@pytest.mark.dependency(depends=["test_base_for_test"])
@pytest.mark.usefixtures("set_log_level")
def test_platform_check_skip_error(tmpdir, runner, base_dir):
    skip_file = str(tmpdir.join("skip.txt"))
    with open(skip_file, mode='w', encoding='utf-8') as file:
        file.write('Справочник.Catalog1.Форма.Form.Форма '
                   'Использование модального вызова: "Предупреждение"\n')
    file.close()

    log = str(tmpdir.join("log.html"))
    argument = ['--debug',
                'platform_check',
                '--connection',
                'File={}'.format(base_dir),
                '--log',
                log,
                '--options',
                '"{}"'.format(options_for_platform_check()),
                '--skip_error',
                skip_file]
    assert runner(argument) == 0
    assert count_lines_in_file(log) == 0


@pytest.mark.dependency(depends=["test_base_for_test"])
@pytest.mark.usefixtures("set_log_level")
def test_platform_dump_config(tmpdir, runner, base_dir):
    folder = str(tmpdir.join("cf"))
    argument = ['--debug',
                'dump_config',
                '--connection',
                'File={}'.format(base_dir),
                '--folder',
                folder]

    assert runner(argument) == 0

    assert os.path.exists(os.path.join(folder,
                                       'DataProcessors',
                                       'DataProcessor1',
                                       'Forms',
                                       'Form',
                                       'Ext',
                                       'Form',
                                       'Module.bsl'))

    version_file = os.path.join(folder, 'ConfigDumpInfo.xml')
    assert os.path.exists(version_file)
