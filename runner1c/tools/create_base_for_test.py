import os
import shutil
import tkinter
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from configparser import ConfigParser

import runner1c


def _ask_directory_click(element, title):
    base_path = filedialog.askdirectory(initialdir=element.get(),
                                        title=title,
                                        mustexist=True)
    if base_path == '':
        return

    _delete_entry_value(element)
    _set_entry_value(element, base_path)


def _place_ask_directory(label_text, position):
    text = label_text + ':'
    label = tkinter.Label(FORM, text=text)
    label.place(x=5, y=position)
    entry = tkinter.Entry(FORM, width=40)
    entry.place(x=5, y=20 + position)
    button = tkinter.Button(FORM, text='...', command=lambda: _ask_directory_click(entry, label_text))
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
THICK_CLIENT = place_checkbox('Толстый клиент', 90, 130)
CREATE_EPF = place_checkbox('Создать epf', 210, 130)
CREATE_CFE = place_checkbox('Создать cfe', 300, 130)


def _set_entry_value(element, text):
    element.insert(0, text)


def _delete_entry_value(element):
    element.delete(0, tkinter.END)


def _radiobutton_change(repo_name):
    _delete_entry_value(BASE)
    _delete_entry_value(PLATFORM)
    _delete_entry_value(REPO)
    THICK_CLIENT.set(False)
    # noinspection PyPep8,PyBroadException
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
                                  command=lambda: _radiobutton_change(repo_name))
    rbutton.place(x=280, y=20 * position)


def _save_parameters(repo_path, base_path, platform_path, thick_client):
    CONFIG.has_option()
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
    txt_stream = open(base_path + '/GitPath.txt', 'w')
    txt_stream.write(repo_path)
    txt_stream.close()


def _create_base_click():
    if not BASE.get():
        messagebox.showerror("Ошибка", 'Не указан путь к базе')
        return

    if not PLATFORM.get():
        messagebox.showerror("Ошибка", 'Не указан путь к платформе')
        return

    if not REPO.get():
        messagebox.showerror("Ошибка", 'Не указан путь к исходникам')
        return

    if os.path.exists(BASE.get()):
        shutil.rmtree(BASE.get(), True)
    os.makedirs(BASE.get())

    argument = ['--debug', 'base_for_test', '--silent', '--path', PLATFORM.get(), '--connection', 'File=' + BASE.get(),
                '--folder', REPO.get()]
    if CREATE_EPF.get():
        argument.append('--create_epf')
    if CREATE_CFE.get():
        argument.append('--create_cfe')
    if THICK_CLIENT.get():
        argument.append('--thick')

    _save_parameters(REPO.get(), BASE.get(), PLATFORM.get(), THICK_CLIENT.get())
    _save_git_path_for_base(BASE.get(), REPO.get())

    if runner1c.core.main(argument) == 0:
        FORM.destroy()


def _create_form():
    FORM.title('Создание базы для тестов')
    FORM.geometry('430x160')

    i = 0
    for key in CONFIG.sections():
        _place_repo(i, key)
        i = i + 1

    create_button = tkinter.Button(FORM,
                                   text='Создать базу',
                                   command=lambda: _create_base_click())
    create_button.place(x=5, y=130)

    FORM.mainloop()


if __name__ == '__main__':
    _create_form()
