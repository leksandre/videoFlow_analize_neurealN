import cv2
import os
import matplotlib.pyplot as plt
import time
import numpy as np
from imageai.Detection import ObjectDetection
from threading import Thread
import requests
import json

import sys



#import logging
#logger = logging.getLogger(__name__)

#logging.basicConfig(
#    level=logging.INFO,
#    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#)






from io import BytesIO
#import m3u8
from PIL import Image
from datetime import datetime
import random
from luckydonaldUtils.encoding import to_binary as b, to_native as n
from luckydonaldUtils.exceptions import assert_type_or_raise
from base64 import b64encode


from ultralytics import YOLO

import torch

from torch import load
from torch.serialization import _load



#os.environ['NNPACK'] = '0'




import ctypes
import logging

# Отключение вывода stderr
libc = ctypes.CDLL("libc.so.6")
STDOUT = 1
STDERR = 2

def suppress_stderr():
    sys.stderr = open(os.devnull, "w")  # Перенаправляем stderr в /dev/null
    libc.dup2(sys.stderr.fileno(), STDERR)  # Заменяем дескриптор

# Возобновление вывода stderr
def unsuppress_stderr():
    sys.stderr.close()
    sys.stderr = sys.__stderr__  # Восстанавливаем оригинальный stderr
    libc.dup2(sys.stderr.fileno(), STDERR)
    
    
    
    
    


# Переопределяем load, чтобы разрешить unsafe глобалы
def unsafe_torch_load(*args, **kwargs):
    kwargs.setdefault('weights_only', False)
    return load(*args, **kwargs)

# Monkey patch
torch._load = unsafe_torch_load
torch.load = unsafe_torch_load


# Путь к папке с моделями
models_folder = "models"




#!!!!!!!!!!!!!!!!!!Name: ultralytics  - Version: 8.3.156

# Перебираем все файлы в папке models
if True:
  for model_file in os.listdir(models_folder):
    if model_file.endswith(".pt"):  # Ищем только .pt файлы
        model_path = os.path.join(models_folder, model_file)
        print(f"Загружаем модель: {model_file}")
        try:
            model = YOLO(model_path)  # Загружаем модель
            print(f"Классы модели '{model_file}':")
            print(model.names)  # Выводим имена классов
            print("-" * 40)
        except Exception as e:
            print(f"Ошибка при загрузке модели {model_file}: {e}")
            



suppress_stderr()
model = YOLO('models/best.pt')
unsuppress_stderr()
print(f"Классы модели 'models/best.pt':")
print(model.names)

num_classes = 10
classes = ['Hardhat', 'Mask', 'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest', 'Person', 'Safety Cone', 'Safety Vest', 'machinery', 'vehicle']




exit()