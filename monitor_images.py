import os
import time
from PIL import Image
from io import BytesIO
import sys
from base64 import b64encode
from datetime import datetime

def to_binary(s):
    return s.encode('utf-8') if isinstance(s, str) else s

def to_native(s):
    return s.decode('utf-8') if isinstance(s, bytes) else s

def get_file(file_path, as_png=True):
    """Читает файл и возвращает его содержимое"""
    if not os.path.exists(file_path):
        return None

    with open(file_path, 'rb') as file:
        content = file.read()

    if not as_png:
        return BytesIO(content)

    try:
        img = Image.open(BytesIO(content))
        output = BytesIO()
        img.save(output, "PNG")
        output.seek(0)
        return output
    except Exception:
        return None

def iterm_show_file(filename, data=None, inline=True, width="auto", height="auto"):
    """Выводит изображение в терминале iTerm2"""
    if data is None:
        with open(filename, 'rb') as f:
            data_bytes = f.read()
    else:
        data_bytes = data.getvalue()

    output = "\033]1337;File=" \
             "name={filename};size={size};inline={inline};" \
             "width={width};height={height}:{data}\a\n".format(
        filename=to_native(b64encode(to_binary(filename))), 
        size=len(data_bytes), 
        inline=1 if inline else 0,
        width=str("50"),
        height=str("50"),
        data=to_native(b64encode(data_bytes)),
    )
    sys.stdout.write(output)
    return output

def monitor_images():
    """Мониторит директорию и выводит новые изображения"""
    image_dir = "/home/Aleksandr/nnfame/img/detection_output"
    last_check = time.time()
    processed_files = set()

    while True:
        now = time.time()
        try:
            # Получаем список PNG-файлов, измененных за последние 10 секунд
            files = [f for f in os.listdir(image_dir) 
                    if f.endswith('.png') and 
                    now - os.path.getmtime(os.path.join(image_dir, f)) <= 10]
            
            # Выводим только новые файлы
            new_files = set(files)
            for filename in new_files:
                filepath = os.path.join(image_dir, filename)
                try:
                    file_content = get_file(filepath)
                    if file_content:
                        #print(f"\nНовое изображение: {filename}") 
                        iterm_show_file(filename, file_content, height=20)
                        #processed_files.add(filename)
                except Exception as e:
                    print(f"Ошибка обработки файла {filename}: {e}")

        except Exception as e:
            print(f"Ошибка при проверке директории: {e}")

        time.sleep(10)  # Точный интервал 10 секунд

if __name__ == "__main__":
    print("Запуск мониторинга изображений...")
    monitor_images()
