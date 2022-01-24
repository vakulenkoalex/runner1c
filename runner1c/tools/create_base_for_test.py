import os
import re
import shutil
import tkinter
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from configparser import ConfigParser

import runner1c


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
CFE_NAME = _place_ask_directory('Путь к feature или epf', 120, True)
THICK_CLIENT = place_checkbox('Толстый клиент', 90, 170)
CREATE_EPF = place_checkbox('Создать epf', 210, 170)


def _set_entry_value(element, text):
    element.insert(0, text)


def _delete_entry_value(element):
    element.delete(0, tkinter.END)


def _radiobutton_change(repo_name):
    _delete_entry_value(BASE)
    _delete_entry_value(PLATFORM)
    _delete_entry_value(REPO)
    THICK_CLIENT.set(False)

    try:
        _set_entry_value(BASE, CONFIG.get(repo_name, 'base'))
        _set_entry_value(PLATFORM, CONFIG.get(repo_name, 'platform'))
        _set_entry_value(REPO, CONFIG.get(repo_name, 'repo'))
        THICK_CLIENT.set(CONFIG.get(repo_name, 'thick_client'))
    except:
        pass


def _place_repo(position, key):
    rbutton = tkinter.Radiobutton(FORM,
                                  text=key,
                                  value=key,
                                  variable=REPO,
                                  command=lambda: _radiobutton_change(key))
    rbutton.place(x=280, y=20 * position)


def _save_parameters(repo_path, base_path, platform_path, thick_client):
    repo_name = os.path.split(repo_path)[1]

    if not CONFIG.has_section(repo_name):
        CONFIG.add_section(repo_name)

    CONFIG.set(repo_name, 'repo', repo_path)
    CONFIG.set(repo_name, 'base', base_path)
    CONFIG.set(repo_name, 'platform', platform_path)
    CONFIG.set(repo_name, 'thick_client', str(thick_client))

    with open(INI_FILE, 'w') as file:
        CONFIG.write(file)
    file.close()


def _save_git_path_for_base(base_path, repo_path):
    txt_stream = open(os.path.join(base_path, 'GitPath.txt'), 'w')
    txt_stream.write(repo_path)
    txt_stream.close()


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

    if CFE_NAME.get():
        extension_name = _get_extension_name_from_file(CFE_NAME.get())
        if len(extension_name) == 0:
            messagebox.showerror("Ошибка", 'В выбраных фичах/тестах нет расширений')
            return

    repo_path = REPO.get()

    if os.path.exists(BASE.get()):
        shutil.rmtree(BASE.get(), True)
    os.makedirs(BASE.get())

    arguments = ['--debug', 'base_for_test', '--path', PLATFORM.get(), '--connection', 'File=' + BASE.get(),
                 '--folder', repo_path]
    if CREATE_EPF.get():
        arguments.append('--create_epf')
    if THICK_CLIENT.get():
        arguments.append('--thick')
    if _folder_for_cfe_exist(repo_path):
        arguments.append('--create_cfe')

    _save_parameters(repo_path, BASE.get(), PLATFORM.get(), THICK_CLIENT.get())
    _save_git_path_for_base(BASE.get(), repo_path)

    if runner1c.core.main(arguments) == 0:
        destroy_form = True
        if CFE_NAME.get():
            arguments = ['--debug', 'add_extensions', '--silent', '--path', PLATFORM.get(), '--connection',
                         'File=' + BASE.get(), '--folder', os.path.join(repo_path, 'spec', 'ext'), '--name',
                         extension_name]
            if runner1c.core.main(arguments) != 0:
                destroy_form = False

        if destroy_form:
            FORM.destroy()


def _create_form():
    FORM.title('Создание базы для тестов ' + runner1c.__version__)
    FORM.geometry('430x200')

    i = 0
    for key in CONFIG.sections():
        _place_repo(i, key)
        i = i + 1

    create_button = tkinter.Button(FORM,
                                   text='Создать базу',
                                   command=lambda: _create_base_click())
    create_button.place(x=5, y=170)

    FORM.mainloop()


if __name__ == '__main__':
    _create_form()
