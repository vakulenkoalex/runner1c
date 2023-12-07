import argparse
import json
import os
import re
import shutil
import tkinter
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from configparser import ConfigParser, NoOptionError

import runner1c
import runner1c.commands.base_for_test as base_for_test
import runner1c.commands.load_extension as load_extension
import runner1c.exit_code as exit_code


def _ask_file_dir(element, title, open_file):
    if open_file:
        path = filedialog.askopenfilenames(initialdir=element.get(),
                                           title=title)
    else:
        path = filedialog.askdirectory(initialdir=element.get(),
                                       title=title,
                                       mustexist=True)
    if path == '':
        return

    _delete_entry_value(element)

    if open_file:
        path_for_element = path[0]
    else:
        path_for_element = path

    _set_entry_value(element, path_for_element.replace('/', '\\'))


def _place_ask_directory(label_text, position, open_file=False):
    text = label_text + ':'
    label = tkinter.Label(FORM, text=text)
    label.place(x=5, y=position)
    entry = tkinter.Entry(FORM, width=40)
    entry.place(x=5, y=20 + position)
    button = tkinter.Button(FORM, text='...', command=lambda: _ask_file_dir(entry, label_text, open_file))
    button.place(x=250, y=18 + position)

    return entry


def place_checkbox(label_text, x, y):
    var = tkinter.IntVar()
    checkbutton = tkinter.Checkbutton(FORM, text=label_text, variable=var)
    checkbutton.place(x=x, y=y)

    return var


INI_FILE = os.path.join(os.getenv('USERPROFILE'), 'base_for_test.ini')
CONFIG = ConfigParser()
CONFIG.read(INI_FILE)
FORM = tkinter.Tk()
BASE = _place_ask_directory('Путь к базе', 0)
PLATFORM = _place_ask_directory('Путь к платформе', 40)
REPO = _place_ask_directory('Путь к исходникам', 80)
EPF_NAME = _place_ask_directory('Путь к feature или epf', 120, True)
CFE_NAME = _place_ask_directory('Путь к расширению с тестами для YAxunit', 160)
YAxunit = _place_ask_directory('Путь к расширению YAxunit', 200)
THICK_CLIENT = place_checkbox('Толстый клиент', 90, 260)
CREATE_EPF = place_checkbox('Создать epf', 210, 260)


def _set_entry_value(element, text):
    element.insert(0, text)


def _delete_entry_value(element):
    element.delete(0, tkinter.END)


def _radiobutton_change(repo_name):
    _delete_entry_value(BASE)
    _delete_entry_value(PLATFORM)
    _delete_entry_value(REPO)
    THICK_CLIENT.set(False)
    _delete_entry_value(YAxunit)

    try:
        _set_entry_value(BASE, CONFIG.get(repo_name, 'base'))
        _set_entry_value(PLATFORM, CONFIG.get(repo_name, 'platform'))
        _set_entry_value(REPO, CONFIG.get(repo_name, 'repo'))
        THICK_CLIENT.set(CONFIG.get(repo_name, 'thick_client'))
        _set_entry_value(YAxunit, CONFIG.get(repo_name, 'yaxunit'))
    except NoOptionError:
        pass


def _place_repo(position, key):
    rbutton = tkinter.Radiobutton(FORM,
                                  text=key,
                                  value=key,
                                  variable=REPO,
                                  command=lambda: _radiobutton_change(key))
    rbutton.place(x=280, y=20 * position)


def _save_parameters(repo_path, base_path, platform_path, thick_client, yaxunit):
    repo_name = os.path.split(repo_path)[1]

    if not CONFIG.has_section(repo_name):
        CONFIG.add_section(repo_name)

    CONFIG.set(repo_name, 'repo', repo_path)
    CONFIG.set(repo_name, 'base', base_path)
    CONFIG.set(repo_name, 'platform', platform_path)
    CONFIG.set(repo_name, 'thick_client', str(thick_client))
    CONFIG.set(repo_name, 'YAxunit', str(yaxunit))

    with open(INI_FILE, 'w') as file:
        CONFIG.write(file)
    file.close()


def _save_parameters_for_acc(base_path, repo_path, platform_path):
    map = {'repo': repo_path, 'platform': platform_path}
    with open(os.path.join(base_path, 'parameters.txt'), 'w') as outfile:
        json.dump(map, outfile)


def _get_extension_name_from_file(file_path):
    path_for_search = file_path

    if os.path.splitext(file_path)[1] == '.epf':
        path_for_search = file_path.replace('build\\', '')
        path_for_search = path_for_search.replace('.epf', '\\Ext\\ObjectModule.bsl')

    array = []
    with open(path_for_search, mode='r', encoding='utf-8') as file:
        for name in re.compile('@Расширение.+', re.MULTILINE).findall(file.read()):
            array.append(name.replace('@', '').replace('Расширение', ''))
    file.close()

    return ','.join(array)


def _folder_for_cfe_exist(repo_path):
    return os.path.exists(os.path.join(repo_path, 'lib', 'ext'))


def _create_base_click():
    extension_name = None

    if not BASE.get():
        messagebox.showerror("Ошибка", 'Не указан путь к базе')
        return
    if not PLATFORM.get():
        messagebox.showerror("Ошибка", 'Не указан путь к платформе')
        return
    if not REPO.get():
        messagebox.showerror("Ошибка", 'Не указан путь к исходникам')
        return
    if EPF_NAME.get():
        extension_name = _get_extension_name_from_file(EPF_NAME.get())
        if len(extension_name) == 0:
            messagebox.showerror("Ошибка", 'В выбраных фичах/тестах нет расширений')
            return

    repo_path = REPO.get()
    if os.path.exists(BASE.get()):
        shutil.rmtree(BASE.get(), True)
    os.makedirs(BASE.get())
    _save_parameters(repo_path, BASE.get(), PLATFORM.get(), THICK_CLIENT.get(), YAxunit.get())
    _save_parameters_for_acc(BASE.get(), repo_path, PLATFORM.get())

    p_test = argparse.Namespace()
    setattr(p_test, 'need_close_agent', False)
    setattr(p_test, 'debug', True)
    setattr(p_test, 'path', PLATFORM.get())
    setattr(p_test, 'connection', 'File=' + BASE.get())
    setattr(p_test, 'folder', repo_path)
    if CREATE_EPF.get():
        setattr(p_test, 'create_epf', True)
    if THICK_CLIENT.get():
        setattr(p_test, 'thick', True)
    else:
        setattr(p_test, 'thick', False)
    if _folder_for_cfe_exist(repo_path):
        setattr(p_test, 'create_cfe', True)

    command = base_for_test.BaseForTest(arguments=p_test)
    return_code = command.execute()
    if exit_code.success_result(return_code):

        success_result = True

        if EPF_NAME.get():
            p_epf = runner1c.command.EmptyParameters(p_test)
            setattr(p_epf, 'connection', 'File=' + BASE.get())
            setattr(p_epf, 'folder', os.path.join(repo_path, 'spec', 'ext'))
            setattr(p_epf, 'name', extension_name)
            setattr(p_epf, 'update', True)
            setattr(p_epf, 'agent', True)
            command_epf = load_extension.LoadExtension(arguments=p_epf, agent_port=command.get_agent_port())
            command_epf.connect_to_agent()
            return_code = command_epf.execute()
            if exit_code.success_result(return_code):
                command_epf.disconnect_from_agent()
            else:
                success_result = False
        if CFE_NAME.get():
            head, tail = os.path.split(CFE_NAME.get())
            p_cfe = runner1c.command.EmptyParameters(p_test)
            setattr(p_cfe, 'connection', 'File=' + BASE.get())
            setattr(p_cfe, 'folder', head)
            setattr(p_cfe, 'name', tail)
            setattr(p_cfe, 'update', True)
            setattr(p_cfe, 'agent', True)
            command_cfe = load_extension.LoadExtension(arguments=p_cfe, agent_port=command.get_agent_port())
            command_cfe.connect_to_agent()
            return_code = command_cfe.execute()
            if exit_code.success_result(return_code):
                command_cfe.disconnect_from_agent()
                if YAxunit.get():
                    head, tail = os.path.split(YAxunit.get())
                    p_yaxunit = runner1c.command.EmptyParameters(p_test)
                    setattr(p_yaxunit, 'connection', 'File=' + BASE.get())
                    setattr(p_yaxunit, 'folder', head)
                    setattr(p_yaxunit, 'name', tail)
                    setattr(p_yaxunit, 'update', True)
                    setattr(p_yaxunit, 'agent', True)
                    command_yaxunit = load_extension.LoadExtension(arguments=p_yaxunit, agent_port=command.get_agent_port())
                    command_yaxunit.connect_to_agent()
                    return_code = command_yaxunit.execute()
                    if exit_code.success_result(return_code):
                        command_yaxunit.disconnect_from_agent()
                    else:
                        success_result = False
            else:
                success_result = False

        if success_result:
            command.close_agent()
            FORM.destroy()


def _create_form():
    FORM.title('Создание базы для тестов ' + runner1c.__version__)
    FORM.geometry('430x300')

    i = 0
    for key in CONFIG.sections():
        _place_repo(i, key)
        i = i + 1

    create_button = tkinter.Button(FORM,
                                   text='Создать базу',
                                   command=lambda: _create_base_click())
    create_button.place(x=5, y=260)

    FORM.mainloop()


if __name__ == '__main__':
    _create_form()
