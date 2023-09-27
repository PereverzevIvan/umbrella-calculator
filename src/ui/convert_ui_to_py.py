# -* coding: utf-8 *-
import os
import re


def generate_all_ui2py(path: str):
    """ Функция для преобразования всех файлов внутри папки с расширением .ui в файлы python """
    files = os.listdir(path)  # Все файлы в папке
    ui_list = []  # Файлы с расширением .ui
    pattern = re.compile(r'.*\.ui')
    for it in files:
        if pattern.match(it):
            ui_list.append(it)
    # Проходимся по всем файлам в папке с расширением .ui
    for it in ui_list:
        # Получаем путь к файлу и генерируем команду для преобразования
        file_path = os.path.join(path, it)
        file_name_without_extension = file_path.split(os.sep)[-1].removesuffix('.ui')
        cmd = f'pyuic5 {file_path} > /home/ivan/Work/Python_projects/UC/umbrella-caclulator/src/modules{os.sep}ui_{file_name_without_extension}.py'
        os.popen(cmd)


if __name__ == '__main__':
    generate_all_ui2py(os.path.dirname((os.path.abspath(__file__))))
