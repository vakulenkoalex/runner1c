# todo убрать задвоенность в test_platform_check
# todo RunShortcut v8i
# todo start without base
# todo dump config update
# todo sync (epf в src)

import os.path

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
    repo_folder = test_dir + '\\repo'
    epf = repo_folder + '\\build\\epf\\ПроверитьКонфигурацию.epf'
    result = str(tmpdir.join("result.txt"))

    argument = ['--debug',
                'base_for_test',
                '--connection',
                'File={}'.format(base_dir),
                '--folder',
                repo_folder,
                '--create_epf']
    assert runner(argument) == 0

    # база создалась
    assert os.path.exists(base_dir)
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
        file.write('Справочник.Справочник1.Форма.ФормаЭлемента.Форма')
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
        file.write('Справочник.Справочник1')
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
        file.write('Справочник.Справочник1.Форма.ФормаЭлемента.Форма '
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
    assert os.path.exists(folder + '\DataProcessors\Обработка1\Forms\Форма\Ext\Form\Module.bsl')