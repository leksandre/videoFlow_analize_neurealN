import cv2
import os
import matplotlib.pyplot as plt
import time
import numpy as np
from imageai.Detection import ObjectDetection
from threading import Thread
import requests
import json
from some import API_KEY, pgdb, pguser, pgpswd, pghost, pgport, pgschema, url_a, url_l, urlD, log_e, pass_e, managers_chats_id, service_chats_id, AppId, login_Analog, pass_Analog, login_Ip, pass_Ip, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, RTSP_URLS
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

# Перебираем все файлы в папке models
if False:
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
model = YOLO('best.pt')
unsuppress_stderr()
print(model.names)

num_classes = 10
classes = ['Hardhat', 'Mask', 'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest', 'Person', 'Safety Cone', 'Safety Vest', 'machinery', 'vehicle']






execution_path = "/home/Aleksandr/nnfame"
execution_image_path = "/home/Aleksandr/nnfame/img"



# Global variables for tracking
probaility = 30
maxPerson = [0, 0]
statObj = [1, 1]
startPoint = [time.time(), time.time()]
PrevDetection = [[], []]
newCols = [[] for _ in range(len(RTSP_URLS))]
access_token = ''


















def send_telegram_alert(detected_objects, image_path, image_path_orig):
    """Отправляет уведомление в Telegram с фотографией"""
    message = "⚠️ Обнаружены нарушения безопасности:\n"
    for obj in detected_objects:
        obj1 = obj["name"]
        message += f"- {obj}\n"
    
    with open("telegram_alerts.log", "a") as log:
        log.write(f"{datetime.now()}: Sent alert for {message}\n")
        
    try:
        # Отправка текстового сообщения
        text_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        text_params = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message
        }
        requests.post(text_url, data=text_params)
        
        # Отправка фотографии
        photo_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': TELEGRAM_CHAT_ID}
            requests.post(photo_url, files=files, data=data)
        with open(image_path_orig, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': TELEGRAM_CHAT_ID}
            requests.post(photo_url, files=files, data=data)
            
        print("Уведомление отправлено в Telegram")
        
    except Exception as e:
        print(f"Ошибка при отправке в Telegram: {e}")
    
    
    
    
    
def get_latest_file(execution_image_path, index, d_cam):
    detection_dir = os.path.join(execution_image_path, 'detection_output')
    
    # Проверяем, существует ли папка
    if not os.path.exists(detection_dir):
        return None

    # Шаблон имени файла: image_{index}_{d_cam}
    target_prefix = f'image_{index}_{d_cam}'

    # Ищем все файлы, начинающиеся с этого префикса
    files = [
        os.path.join(detection_dir, f) for f in os.listdir(detection_dir)
        if f.startswith(target_prefix)
    ]

    # Фильтруем только файлы (не папки) и сортируем по времени изменения
    files = [f for f in files if os.path.isfile(f)]
    
    if not files:
        return None  # Файлы не найдены

    # Возвращаем самый свежий файл
    latest_file = max(files, key=os.path.getmtime)
    return latest_file
    
    
    
      
      
# Function to check and create columns in the database
def checkAndCreateColumn(index, nameCol):
    global structable, newCols
    if not structable or not isinstance(structable, list):
        return
    colNameExist = any(col['name'] == nameCol for col in structable)
    if not colNameExist and not nameCol in newCols[index]:
        Headers = {'Authorization': f"Bearer {access_token}", 'Content-Type': 'application/x-www-form-urlencoded'}
        maindata = f"tableName=statofobjects&json=%5B%7B%22name%22%3A%22{nameCol}%22%2C%22type%22%3A%22text%22%7D%5D"
        r = simpleRequest(url=urlD + url_l + '/' + str(listId) + '/newcolumn', headers=Headers, data=maindata)
        newCols[index].append(nameCol)

# Function to compare detections
def compare_persons(list1, list2):
    stat1 = 0
    if isinstance(list1, list) and isinstance(list2, list):
        if len(list1) != len(list2):
            print(f"Различное количество элементов")
        for i in range(len(list1)):
            doNotMove = False
            for j in range(len(list2)):
                if list1[i]['box_points'] == list2[j]['box_points']:
                    doNotMove = True
                    print(f"!!!------Объект без движения: {list1[i]}")
                    print(f"!!!------Объект без движения: {list2[j]}")
            if doNotMove:
                stat1 += 1
    print(f"Объектов без движения: {stat1}")
    return stat1

def get_file(file_path, as_png=True):
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return None

    try:
        with open(file_path, 'rb') as file:
            content = file.read()

        fake_input = BytesIO(content)
        fake_input.seek(0)
        
        if not as_png:
            return fake_input

        im = Image.open(fake_input)
        del fake_input
        fake_output = BytesIO()
        im.save(fake_output, "PNG")
        del im
        fake_output.seek(0)
        return fake_output
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return None

# Function to fix statistics
def fixStatistic(index, maxPerson, statObj):
    global access_token, listId
    now_1 = datetime.now()
    time_1 = now_1.strftime("%H:%M:%S")
    date_1 = now_1.strftime("%Y-%m-%d")
    Headers = {'Authorization': f"Bearer {access_token}", 'Content-Type': 'application/x-www-form-urlencoded'}
    maindata = f"listId={listId}&tableName=statofobjects&json=%7B%22date%22%3A%22{date_1}%22%2C%22time%22%3A%22{time_1}%22%2C%22person%22%3A%22{maxPerson}%22%2C%22person_avg%22%3A%22{statObj}%22%7D"
    r = simpleRequest(url=urlD + (url_l[:-1]), headers=Headers, data=maindata, showresp=True)

# Function to process each video stream


def is_intersecting(box1, box2):
    """Проверяет пересекаются ли два bounding box'а"""
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    
    # Проверка пересечения по оси X
    if max(x1_min, x2_min) > min(x1_max, x2_max):
        return False
    
    # Проверка пересечения по оси Y
    if max(y1_min, y2_min) > min(y1_max, y2_max):
        return False
    
    # Если обе проверки пройдены, прямоугольники пересекаются
    return True

    # Проверяем пересечение по осям X и Y
    #x_intersection = x1_max >= x2_min and x2_max >= x1_min
    #y_intersection = y1_max >= y2_min and y2_max >= y1_min
    
    #return x_intersection and y_intersection
    
    
def process_stream(index, rtsp_url, weights, threshold, d_cam):
    global maxPerson, statObj, startPoint, PrevDetection, newCols, access_token
    
    print(f"Запущен поток: {index}, камера: {d_cam}, URL: {rtsp_url}, Камер: {weights}, Порог: {threshold}")

    # Определяем тип URL и формируем правильный поток
    if "user=admin" in rtsp_url and "channel=" in rtsp_url:
        # Для камер основной линейки
        if d_cam=="":
            d_cam =0
        stream_url = rtsp_url.replace("channel=1", f"channel={d_cam+1}")  # каналы обычно начинаются с 1
    elif "@" in rtsp_url and "mpeg4" in rtsp_url:
        # Для камер 7-ой серии (PN7X...)
        stream_url = rtsp_url.replace("mpeg4", f"mpeg4/ch{d_cam+1}/main")  # предполагаем структуру URL
    elif "chID=" in rtsp_url and "streamType=" in rtsp_url:
        # Для регистраторов серии PVNR-9X-XX
        stream_url = rtsp_url.replace("chID=1", f"chID={d_cam+1}")
    else:
        # Стандартный RTSP поток (как в исходном коде)
        stream_url = f"{rtsp_url}{d_cam}" if d_cam != 0 else rtsp_url
        
    print(f"[Поток {index}-#{d_cam}] Попытка открыть: {stream_url}"+"\n\n")




    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print(f"Failed to open stream {stream_url}")
        return
    
    last_cap_time = time.time()
    
    #print(f"000\n\n")
    cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Уменьшаем размер буфера
    cap.set(cv2.CAP_PROP_FPS, 10)  # Устанавливаем разумный FPS

        

    #print(f"0001111\n\n")
    while True:
    
        #print(f"000222\n\n")
        if time.time() - last_cap_time > 30:  # Каждые 30 секунд
            cap.release()
            cap = cv2.VideoCapture(stream_url)
            cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Уменьшаем размер буфера
            cap.set(cv2.CAP_PROP_FPS, 10)  # Устанавливаем разумный FPS
 
            last_cap_time = time.time()
        #print(f"111\n\n")
        # Очищаем буфер кадров
        for _ in range(20):  # Пропускаем несколько кадров
          if not cap.grab():
            #print("Ошибка grab()")
            continue
        
        # Получаем актуальный кадр
        ret, frame = cap.retrieve()
        
        if not ret:
            print(f"Failed to read frame from stream {stream_url}")
            time.sleep(5)  # Пауза перед повторной попыткой
            continue
                
        way1 = os.path.join(execution_image_path, f'image_{index}_{d_cam}.png')
        #print(f"222\n\n")
        cv2.imwrite(way1, frame, [cv2.IMWRITE_PNG_COMPRESSION, 1])

        if False:
            try:
                img = Image.open(way1) 
                img.verify()  
                #print("Файл в порядке")
            except Exception as e:
                print("Файл повреждён:", e)
                try:
                    img = Image.open(way1) 
                    img.save(way1)
                    print("Файл сохранен")
                except Exception as e2:
                    print("Файл не исправен:", e2)
                    time.sleep(5)
                    continue

        #print('writed 1 ', way1)
        #print(f"333\n\n")
        try:
            results = model.predict(source=way1, save=True, save_txt=True,  project=execution_image_path, name='detection_output',  exist_ok=True )
            
            way2 = get_latest_file(execution_image_path, index, d_cam)
            if way2:
                #print("Найден последний файл:", way2)
                pass
            else:
                way2 = os.path.join(execution_image_path, 'detection_output', f'image_{index}_{d_cam}.jpg')
                
            detections = []
            violations = [] 
            persons = []
            #print(f"444\n\n")
            for result in results:
                boxes = result.boxes  # Это объект Boxes
                if boxes is not None:
                    for box in boxes:
                        # Конвертируем координаты в список чисел
                        bbox = box.xyxy.cpu().numpy().astype(int).tolist()[0]
                        conf = float(box.conf.cpu().numpy()[0])
                        cls_id = int(box.cls.cpu().numpy()[0])

                        obj_name = classes[cls_id]
                        detection = {
                            "name": obj_name,
                            "percentage_probability": conf * 100,
                            "box_points": bbox
                        }
                        
                        if obj_name in ['NO-Hardhat', 'NO-Safety Vest']:
                            violations.append(detection)
                        
                        if obj_name == 'Person':
                            persons.append(detection)
                            
                        detections.append(detection)



            real_violations = []
            for violation_box in violations:
                for person_box in persons:
                    if is_intersecting(violation_box['box_points'], person_box['box_points']):
                        violation_type = violation_box['name']
                        real_violations.append(f"{violation_type} (на человеке)")
                        break  # Достаточно одного пересечения
            
            # Отправляем уведомление только о реальных нарушениях
            if real_violations:
                # Отправляем уведомление
                send_telegram_alert(violations, way2, way1)
        
            if detections:
                #print("Объекты найдены!!! -------------------------------")
                
                #image = Image.open(way2)
                #plt.imshow(image)
                #plt.grid(False)
                #plt.show()
                
                if False:
                    file_content = get_file(file_path=way2, as_png=True)
                    image=iterm_show_file(way2, data=file_content, inline=True, height=50)
            
                
            
            

        except Exception as e:
            print(f"Ошибка при обработке изображения: {e}")




        time.sleep(5)
        

def iterm_show_file(filename, data=None, inline=True, width="auto", height="auto", preserve_aspect_ratio=True):
    """

    https://iterm2.com/documentation-images.html
    
    :param filename: 
    :param data: 
    :param inline: 
    :param width:  
    :param height: 
    :param preserve_aspect_ratio: 
    
    Size:
        - N   (Number only): N character cells.
        - Npx (Number + px): N pixels.
        - N%  (Number + %):  N percent of the session's width or height.
        - auto:              The image's inherent size will be used to determine an appropriate dimension.
    :return: 
    """
    width = str(width) if width is not None else "auto"
    height = str(height) if height is not None else "auto"
    if data is None:
        data = read_file_to_buffer(filename)
    # end if
    data_bytes = data.getvalue()
    output = "\033]1337;File=" \
             "name={filename};size={size};inline={inline};" \
             "preserveAspectRatio={preserve};width={width};height={height}:{data}\a\n".format(
        filename=n(b64encode(b(filename))), size=len(data_bytes), inline=1 if inline else 0,
        width=width, height=height, preserve=1 if preserve_aspect_ratio else 0,
        data=n(b64encode(data_bytes)),
    )
    sys.stdout.write(output)
    return output
# end if
      
def checkImg(pp=probaility,img1='',name1="image_1new"):
    
    global maxPerson
    global statObj
    global startPoint
    global PrevDetection
    
    start_time = time.time() 
    # predictions, probabilities = detector.classifyImage(os.path.join(execution_image_path , "image1.png"), result_count=20)
    
    detections = detector.detectObjectsFromImage(input_image=os.path.join(execution_image_path , "image1.png"), output_image_path=os.path.join(execution_image_path , "imagenew.png"), minimum_percentage_probability=30)

    end_time = time.time()  # время окончания выполнения
    execution_time = end_time - start_time  # вычисляем время выполнения
    print(f"- Время распознования: {execution_time} секунд")
    
    global newCols
    
    for eachObject in detections:
        print(eachObject["name"] , " : ", eachObject["percentage_probability"], " : ", eachObject["box_points"] )
        
        print("--------------------------------")
        if eachObject["name"]!='person':
            if not eachObject["name"] in newCols:
                checkAndCreateColumn(eachObject["name"])
                newCols.append(eachObject["name"])
    
    
  
        
    
    
    
    # for eachObject in detections:
    #     if eachObject["name"]=='person':
    #         personCount = 1+personCount    
            
    CurDetection = detections
    filtered_data_cur = [item for item in CurDetection if item['name'] == 'person']
    personCount = len(filtered_data_cur)
    
    diffStat = 0
    if PrevDetection:
        filtered_data_prev = [item for item in PrevDetection if item['name'] == 'person']
        diffStat = compare_persons(filtered_data_prev,filtered_data_cur)
    
    if diffStat>0:
        statObj = statObj * (1 - (diffStat/personCount) )

        # print(eachObject["box_points"][0] )
        # print(eachObject["box_points"][1] )
        # print(eachObject["box_points"][2] )
        # print(eachObject["box_points"][3] )
    
    
    if maxPerson<personCount:
        maxPerson=personCount
    
    total_time =  start_time - startPoint
    print(f"maxPerson,statObj,total_time {maxPerson,statObj,total_time}")
    if total_time>(60*eachMin):
        fixStatistic(maxPerson,statObj)
        startPoint = time.time() 
        maxPerson = 0
        statObj = 1
    else:
        time.sleep(5)
    
    PrevDetection = CurDetection
        



def simpleRequest(isGet = False, checkStruct = False, showresp = False, **params):
        try:
            if isGet:
                r = requests.get(**params)
            else:
                # print('post params',params)
                r = requests.post(**params)
        except requests.exceptions.RequestException as err:
            print("__OOps: Something Else", err)
            #return Response1("201", '')
            return False
        except requests.exceptions.HTTPError as errh:
            print("__Http Error:", errh)
            #return Response1("201", '')
            return False
        except requests.exceptions.ConnectionError as errc:
            print("__Error Connecting:", errc)
            #return Response1("201", '')
            return False
        except requests.exceptions.Timeout as errt:
            print("__Timeout Error:", errt)
            #return Response1("201", '')
            return False
        except KeyError as e:
            print(' over KeyError  ' + str(e))
            #return Response1("201", '')
            return False
        if showresp:
            print('result text:'+str(r.text))
            print('response:', (r))
            print('response type:', type(r))
        
        print('status_code:'+str(r.status_code))
        
        
        
        
        if r.status_code != 200:
            print('text:'+str(r.text)[0:2000])
            return False
        
        d = json.JSONDecoder()
        
        try:
            data = json.loads(r.text)
        except json.JSONDecodeError:
            print(' not json 0 ' + str(r.text)[0:2000])
            return 0
        
        if checkStruct:
            if not 'data' in data:
                print(' not data 0 ' + str(data))
                return False
            if not 'meta' in data:
                print(' not meta 0 ' + str(data))
                return False
            for dataList in data['data']:
                print(' data[data] ',dataList)
        
        return r

def getListId(tables=[]):
    global structable
    # print('access_token',access_token)
    Headers = { 'Authorization' : "Bearer "+str(access_token) }
    
    listId = 0
    
    r = simpleRequest(isGet=True, url = urlD+url_l+"?page=1&pageSize=100&appId="+str(AppId), headers=Headers)
    data = r.json()

    for dataList in data['data']:
        # print('dataList',dataList)
        # print('dataList name',dataList['attributes']['name'])    
        # print('dataList satatus',dataList['attributes']['status'])
        if dataList['attributes']['name']=='statistic':
            listId = dataList['id']
            for table in dataList['attributes']['structure']['tables']:
                if table['name']=='statofobjects':
                    structable = table['fields'] 
                    tables.append('statofobjects')
    return listId
                
def checkAndCreateList():
    global access_token
    global listId
    
    PARAMS = {'login':log_e,'password':pass_e}
    url_e = urlD+(url_a.replace('userLogin555',log_e)).replace('userPassword888',pass_e)
    
    r = simpleRequest(isGet=True, url = url_e, params = PARAMS)
    data = r.json()
    if not 'access_token' in data:
        print(' not access_token ' + str(data))
        return False
    try:
        access_token = data['access_token']
        refresh_token = data['refresh_token']
        # print(data,access_token,refresh_token)
    except KeyError as e:
        print(' over KeyError 43 ' + str(e))
        return False

    
    listId = getListId()
    
    Headers = { 'Authorization' : "Bearer "+str(access_token), 'Content-Type': 'application/x-www-form-urlencoded' }
    
    if listId == 0 :
        # createList
        maindata = 'AppId='+str(AppId)+'&name=statistic&description=stat+data+from+ours+camera&structure=%7B%22links%22%3A%5B%5D%2C%22tables%22%3A%5B%5D%7D'
        r = simpleRequest(url=urlD+url_l, headers=Headers, data=maindata)
    tables = []    
    listId = getListId(tables)
    if listId == 0 :
        print(' List not created ' + str(urlD))
        return False

    if len(tables)==0:
        #createTable
        maindata = 'json=%5B%7B%22name%22%3A%22statofobjects%22%2C%22fields%22%3A%5B%7B%22name%22%3A%22date%22%2C%22type%22%3A%22text%22%7D%2C%7B%22name%22%3A%22time%22%2C%22type%22%3A%22text%22%7D%2C%7B%22name%22%3A%22person%22%2C%22type%22%3A%22text%22%7D%2C%7B%22name%22%3A%22person_avg%22%2C%22type%22%3A%22text%22%7D%5D%7D%5D'
        r = simpleRequest(url=urlD+url_l+'/'+str(listId)+'/newtable', headers=Headers, data=maindata)
    tables = []
    listId = getListId(tables)
    if len(tables)==0:
        print(' table not created ' + str(urlD))
        return False
    return True

            

def restartable_thread(target, args=()):
    """Функция, которая перезапускает поток при его завершении"""
    #print(f"пытаюсь запустить поток 0 : ")
    def wrapper():
        #print(f"пытаюсь запустить поток 1 : ")
        while True:
            #print(f"пытаюсь запустить поток 2 : ")
            try:
                #print(f"пытаюсь запустить поток Старт: ")
                target(*args)
            except Exception as e:
                print(f"[Ошибка в потоке] {e}. Перезапуск через 30 секунд...")
                time.sleep(30)
    thread = Thread(target=wrapper, daemon=True)
    return thread




def main():
    global access_token, listId, structable

    if not checkAndCreateList():
        print('checkAndCreateList - fail')
        exit()

    threads = []
    for rtsp_info in RTSP_URLS:  
       #for d in range(rtsp_info["weights"]):
       for d in (rtsp_info["viwes"]):
       
       # thread = Thread(
       #     target=process_stream,
       #     args=(rtsp_info["name"], rtsp_info["url"], rtsp_info["weights"], rtsp_info["threshold"], d)
       # )
       
        name = rtsp_info["name"]
        url = rtsp_info["url"]
        weights = rtsp_info["weights"]
        threshold = rtsp_info["threshold"]
        thread = restartable_thread(
            target=process_stream,
            args=(name, url, weights, threshold, d)
        )
        
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
        


    # Бесконечный цикл, чтобы основной поток не завершался
    try:
      while True:
        print('threading.active_count() ',threading.active_count())   
        while threading.active_count() > 1:
            print('threading.active_count() ',threading.active_count())
            time.sleep(30)
    except KeyboardInterrupt:
        print("Остановка программы.")
        
        
        
if __name__ == "__main__":
    main()
