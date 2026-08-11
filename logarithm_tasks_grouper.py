import os
import re
import subprocess
import shutil
import glob
clear = lambda: os.system('cls')
dir_path = os.path.dirname((os.path.abspath(__file__)))
def is_logarithm_task(task):
    # Skip tasks containing specific keywords
    included_keywords = ['^']
    excluded_keywords = ['\\cos', '\\sin', '\\log', '\\lg', '\\tan', '\\tg', '\\sqrt']
    
    # Check if the task contains the power symbol (^)
    if any(keyword in task for keyword in included_keywords):
        # Make sure it doesn't contain any of the excluded keywords
        if not any(keyword in task for keyword in excluded_keywords):
            return True
    
    return True  # Return False for all other tasks  # Return False for all other tasks
def extract_tasks(tex_content):
    task_pattern = re.compile(r'\\item\s*(.*?)(?=\\item|\Z)', re.DOTALL)
    return task_pattern.findall(tex_content)

def read_file_with_encoding(file_path, encodings=['utf-8', 'windows-1251', 'cp866']):
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to read the file with any of the encodings: {encodings}")

def group_logarithm_tasks(input_file, output_file):
    tex_content = read_file_with_encoding(input_file)

    tasks = extract_tasks(tex_content)
    logarithm_tasks = [task for task in tasks if is_logarithm_task(task)]
    
    # Группируем задачи по числу в начале номера
    task_groups = {}
    for task in logarithm_tasks:
        match = re.match(r'\[(\d+)', task)
        if match:
            group_number = match.group(1)
            if group_number not in task_groups:
                task_groups[group_number] = []
            task_groups[group_number].append(task)

    # Сортируем группы по номеру
    sorted_groups = sorted(task_groups.items(), key=lambda x: int(x[0]))

    # Каждая группа становится отдельным блоком
    blocks = [group for _, group in sorted_groups]

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\\documentclass{article}\n\\usepackage[utf8]{inputenc}\n\\usepackage[T2A]{fontenc}\n\\usepackage{amsmath}\n\\begin{document}\n\n")
        for i, block in enumerate(blocks, 1):
            f.write(f"\\section*{{Блок {i}}}\n\n\\begin{{enumerate}}\n")
            for task in block:
                f.write(f"\\item {task.strip()}\n")
            f.write("\\end{enumerate}\n\n\\noindent\\rule{\\textwidth}{0.4pt}\n\n")
        f.write("\\end{document}")

    return blocks

def cleanup_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(('.aux', '.log', '.out', '.synctex.gz')):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                print(f"Удален файл: {file_path}")
            except Exception as e:
                print(f"Ошибка при удалении файла {file_path}: {str(e)}")

def create_student_tex(tasks, student_number, output_folder):
    tex_content = r"\documentclass[a4paper,10pt]{article}" + "\n"
    tex_content += r"\usepackage[utf8]{inputenc}" + "\n"
    tex_content += r"\usepackage[T2A]{fontenc}" + "\n"
    tex_content += r"\usepackage[russian]{babel}" + "\n"
    tex_content += r"\usepackage{amsmath}" + "\n"
    tex_content += r"\usepackage{amssymb}" + "\n"
    tex_content += r"\usepackage{multicol}" + "\n"
    tex_content += r"\usepackage{graphicx}" + "\n"
    tex_content += r"\usepackage[left=1cm,right=1cm,top=1cm,bottom=2cm]{geometry}" + "\n"
    tex_content += r"\begin{document}" + "\n\n"
    tex_content += r"\begin{center}\Large\textbf{Вариант " + f"{student_number}" + r"}\end{center}" + "\n\n"
    tex_content += r"\begin{enumerate}" + "\n"
    for i, (task, variant) in enumerate(tasks, 1):
        # Удаляем встроенную нумерацию и лишние фразы
        task = re.sub(r'^\[\d+\.\d+\]', '', task)
        task = re.sub(r'y={{', 'y=', task)
        # Заменяем фразу "Если уравнение имеет более одного корня," на перенос строки и условие
        task = task.replace("Если уравнение имеет более одного корня,", r"\\").strip()
        
        # Удаляем фразу "найдите значение выражения" и её вариации
        task = re.sub(r'Найдите значение выражения[:\s]*', '', task)
        
        # Удаляем все вхождения \begin{enumerate} и \end{enumerate}
        task = re.sub(r'\\begin\{enumerate\}|\\end\{enumerate\}', '', task)
        
        # Заменяем все варианты width=0.5\textwidth на width=0.2\textwidth
        task = re.sub(r'width=0\.5\\textwidth', r'width=0.2\\textwidth', task)
        
        task = re.sub(r'width=0\.5\\textwidth', r'width=0.2\\textwidth', task)
        task = re.sub(r'\[width=0\.5\]', r'[width=0.2]', task)
        task = re.sub(r'width=0\.5', r'width=0.2', task)
        
        # Также обрабатываем случай, когда width указан без \textwidth
        task = re.sub(r'\[width=0\.5\]', r'[width=0.2]', task)
        # Обрабатываем случай, когда width указан в других форматах
        task = re.sub(r'width=0\.5', r'width=0.2', task)
        
        # Добавляем \vspace перед и после изображений
        task = re.sub(r'(\\includegraphics)', r'\\vspace{3mm}\1', task)
        task = re.sub(r'(\\includegraphics.*?\})', r'\1\\vspace{3mm}', task)

        # Удаляем лишние пробелы и переносы строк
        
        tex_content += f"\\item {task}\n\n"

    
    tex_content += r"\end{enumerate}" + "\n"
    tex_content += r"\end{document}"
    
    file_path = os.path.join(output_folder, f"student_{student_number}.tex")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(tex_content)
    
    return file_path

def convert_tex_to_pdf(tex_file):
    pdflatex_path = f"{dir_path}\pdflatex.exe"

    if not os.path.exists(pdflatex_path):
        print(f"Файл pdflatex не найден по пути: {pdflatex_path}")
        print("Убедитесь, что MiKTeX установлен и путь указан верно.")
        return

    try:
        result = subprocess.run([pdflatex_path, '-interaction=nonstopmode', '-output-directory', os.path.dirname(tex_file), tex_file], 
                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"Создан PDF файл: {os.path.splitext(tex_file)[0]}.pdf")
        return
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при конвертации {tex_file} в PDF")
        print(f"Код ошибки: {e.returncode}")
        print(f"Вывод команды:")
        print(e.output)
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

    print("Убедитесь, что MiKTeX установлен корректно и все необходимые пакеты установлены.")

def create_all_variants_tex(all_student_tasks, output_folder):
    tex_content = r"\documentclass[a4paper,10pt]{article}" + "\n"
    tex_content += r"\usepackage[utf8]{inputenc}" + "\n"
    tex_content += r"\usepackage[T2A]{fontenc}" + "\n"
    tex_content += r"\usepackage[russian]{babel}" + "\n"
    tex_content += r"\usepackage{amsmath}" + "\n"
    tex_content += r"\usepackage{amssymb}" + "\n"
    tex_content += r"\usepackage{multicol}" + "\n"
    tex_content += r"\usepackage{graphicx}" + "\n"
    tex_content += r"\usepackage[left=1cm,right=1cm,top=1cm,bottom=2cm]{geometry}" + "\n"
    tex_content += r"\begin{document}" + "\n\n"
    tex_content += r'\begin{center}\Large\textbf{Задачи B12}\end{center}'
    tex_content += r'\begin{center}\Large\textbf{Производные}\end{center}'
    tex_content += r'\newpage' "\n"
    # Start multicols once at the beginning

    for student_number, tasks in enumerate(all_student_tasks, 1):
        tex_content += r"\begin{center}\large\textbf{Вариант " + f"{student_number}" + r"}\end{center}" + "\n\n"
        tex_content += r"\begin{enumerate}" + "\n"
        for task, variant in tasks:
            task = re.sub(r'^\[\d+\.\d+\]', '', task)
            task = re.sub(r'\\begin\{enumerate\}|\\end\{enumerate\}', '', task)
            task = re.sub(r'Найдите значение выражения[:\s]*', '', task)
                        # Ensure width replacement
            task = re.sub(r'width=0\.5\\textwidth', r'width=0.2\\textwidth', task)
            task = re.sub(r'\[width=0\.5\]', r'[width=0.2]', task)
            task = re.sub(r'width=0\.5', r'width=0.2', task)
            task = re.sub(r'y={{', 'y=', task)
            tex_content += f"\\item {task}\n\n"
   
        tex_content += r"\end{enumerate}" + "\n"
        
        tex_content += r'\vspace{3mm}' + "\n"
        # Add newpage after each variant
        tex_content += r"\newpage" + "\n\n"

    # End multicols once at the end
    tex_content += r"\end{document}"

    file_path = os.path.join(output_folder, "all_variants.tex")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(tex_content)

    return file_path

def generate_variants(num_students, task_blocks):
    base_folder = f"{dir_path}\log_variants"
    tex_folder = os.path.join(base_folder, "tex")
    pdf_folder = os.path.join(base_folder, "pdf")

    # Создаем папки, если они не существуют
    for folder in [base_folder, tex_folder, pdf_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    all_student_tasks = []

    for j in range(num_students):
        student_tasks = []
        for i, block in enumerate(task_blocks):
            task_numbers_list_spec = list(range(1, len(block) + 1))
            
            if len(task_numbers_list_spec) == 1:
                variant = task_numbers_list_spec[0]
            elif j == 0:
                if task_numbers_list_spec[num_students % len(task_numbers_list_spec)] == task_numbers_list_spec[0]:
                    variant = task_numbers_list_spec[1]
                else:
                    variant = task_numbers_list_spec[num_students % len(task_numbers_list_spec)]
            elif task_numbers_list_spec[j % len(task_numbers_list_spec)] == task_numbers_list_spec[0]:
                variant = task_numbers_list_spec[1]
            else:
                variant = task_numbers_list_spec[j % len(task_numbers_list_spec)]
            
            task = block[variant - 1]  # Индексы в Python начинаются с 0
            student_tasks.append((task, variant))
        
        all_student_tasks.append(student_tasks)
        
        tex_file = create_student_tex(student_tasks, j+1, base_folder)
        print(f"Создан файл: {tex_file}")
        convert_tex_to_pdf(tex_file)

    # Создаем файл со всеми вариантами
    all_variants_tex = create_all_variants_tex(all_student_tasks, base_folder)
    print(f"Создан файл со всеми вариантами: {all_variants_tex}")
    convert_tex_to_pdf(all_variants_tex)

    # Перемещаем файлы в соответствующие папки
    for filename in os.listdir(base_folder):
        if filename.endswith('.tex'):
            shutil.move(os.path.join(base_folder, filename), os.path.join(tex_folder, filename))
        elif filename.endswith('.pdf'):
            shutil.move(os.path.join(base_folder, filename), os.path.join(pdf_folder, filename))

    cleanup_files(base_folder)
    cleanup_files(tex_folder)
    cleanup_files(pdf_folder)
    #clear()
    print(f"Варианты для {num_students} учеников созданы в папке '{base_folder}'")
    print(f"TEX файлы находятся в папке: {tex_folder}")
    print(f"PDF файлы находятся в папке: {pdf_folder}")
def cleanup_old_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(('.pdf', '.tex')):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                print(f"Удален старый файл: {file_path}")
            except Exception as e:
                print(f"Ошибка при удалении файла {file_path}: {str(e)}")

def cleanup_output_file(base_folder, tex_folder):
    output_file_base = os.path.join(base_folder, "output.tex")
    output_file_tex = os.path.join(tex_folder, "output.tex")
    
    for file_path in [output_file_base, output_file_tex]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Удален файл: {file_path}")
            except Exception as e:
                print(f"Ошибка при удалении файла {file_path}: {str(e)}")


def find_tex_file(directory):
    tex_files = glob.glob(os.path.join(directory, '*.tex'))
    if not tex_files:
        raise FileNotFoundError("Не найден .tex файл в папке программы")
    if len(tex_files) > 1:
        print("Найдено несколько .tex файлов. Используется первый найденный файл.")
    return tex_files[0]
if __name__ == "__main__":
    input_file = find_tex_file(dir_path)
    base_folder = os.path.join(dir_path, "log_variants")
    tex_folder = os.path.join(base_folder, "tex")
    pdf_folder = os.path.join(base_folder, "pdf")
    output_file = os.path.join(base_folder, "output.tex")

    # Создаем папки, если они не существуют
    for folder in [base_folder, tex_folder, pdf_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Очищаем старые файлы
    cleanup_old_files(tex_folder)
    cleanup_old_files(pdf_folder)

    try:
        task_blocks = group_logarithm_tasks(input_file, output_file)
        print(f"Задачи с логарифмами сгруппированы и сохранены в файл {output_file}")
        #clear()
        num_students = int(input("Введите количество учеников: "))
        generate_variants(num_students, task_blocks)

        # Удаляем output.tex после завершения работы
        cleanup_output_file(base_folder, tex_folder)
    except Exception as e:
        print(f"Произошла ошибка: {e}")