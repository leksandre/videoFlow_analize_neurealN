import cv2
import os
import time
import numpy as np
from imageai.Detection import ObjectDetection
from threading import Thread
import requests
import json
from some import API_KEY, pgdb, pguser, pgpswd, pghost, pgport, pgschema, url_a, url_l, urlD, log_e, pass_e, managers_chats_id, service_chats_id, AppId

from io import BytesIO
import m3u8
from PIL import Image
from datetime import datetime
import random
from luckydonaldUtils.encoding import to_binary as b, to_native as n
from luckydonaldUtils.exceptions import assert_type_or_raise
from base64 import b64encode

from ultralytics import YOLO

model = YOLO('best.pt')


# Initialize the object detection model
#detector = ObjectDetection()
#detector.setModelTypeAsYOLOv3()
#detector.setModelPath(os.path.join(os.getcwd(), "pretrained-yolov3.h5"))
#detector.setModelPath(os.path.join(os.getcwd(), "best_Construction_Equipment.v6i-constructionequipment-ejop6.pt"))
#detector.setModelPath(os.path.join(os.getcwd(), "best.pt"))
#detector.loadModel()

# Define RTSP URLs
# RTSP_URLS = [
#     "rtsp://adminn:12345q@192.168.1.12:554/stream",
#     "rtsp://admin:12345q@192.168.1.56:554/stream"
# ]

execution_path = "/home/Aleksandr/nnstream"
execution_image_path = "/home/Aleksandr/nnstream/img"

RTSP_URLS = [
    {
        "name": "Analog",
        "url": "rtsp://adminn:12345q@192.168.1.12:554/stream",
        "weights": 3,
        "threshold": 0.3
    },
    {
        "name": "IP",
        "url": "rtsp://admin:12345q@192.168.1.56:554/stream",
        "weights": 16,
        "threshold": 0.3
    }
]

# Global variables for tracking
probaility = 30
maxPerson = [0, 0]
statObj = [1, 1]
startPoint = [time.time(), time.time()]
PrevDetection = [[], []]
newCols = [[] for _ in range(len(RTSP_URLS))]
access_token = ''

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

    with open(file_path, 'rb') as file:
        content = file.read()

    fake_input = BytesIO(content)
    fake_input.seek(0)
    if not as_png:
        return fake_input
    # end if

    im = Image.open(fake_input)
    del fake_input
    fake_output = BytesIO()
    im.save(fake_output, "PNG")
    del im
    fake_output.seek(0)
    return fake_output
# end def

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
def process_stream(index, rtsp_url, weights, threshold, d_cam):
    global maxPerson, statObj, startPoint, PrevDetection, newCols, access_token
    
    print(f"Запущен поток: {index}, камера: {d_cam}, URL: {rtsp_url}  {d_cam}, Камер: {weights}, Порог: {threshold}")

    if 1:
        stream_url = f"{rtsp_url}{d_cam}"
        
        # if d_cam==0:
        #     stream_url = f"{rtsp_url}"
        
        print(f"[Поток {index}-#{d_cam}] Попытка открыть: {stream_url}")

        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            print(f"Failed to open stream {rtsp_url}{d_cam}")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"Failed to read frame from stream {rtsp_url}{d_cam}")
                break
                
            way1 = os.path.join(execution_image_path , f'image_{index}_{d_cam}.png')
            way2 = os.path.join(execution_image_path , f'image_{index}_{d_cam}_new.png')
            
            cv2.imwrite(way1, frame, [cv2.IMWRITE_PNG_COMPRESSION, 1])
            



            try:
                img = Image.open(way1) 
                img.verify()  
                print("Файл в порядке")
            except Exception as e:
                print("Файл повреждён:", e)
                try:
                    img = Image.open(way1) 
                    img.save(way1)
                    print("Файл сохранен")
                except Exception as e2:
                    print("Файл не исправен:", e2)
                    break


            print('writed 1 ',way1)
            detections = detector.detectObjectsFromImage(input_image=way1, output_image_path=way2, minimum_percentage_probability=30)

            print('writed 2 ',way2)
   
            
            for eachObject in detections:
                print(eachObject["name"], " : ", eachObject["percentage_probability"], " : ", eachObject["box_points"])
                print("--------------------------------")
                if eachObject["name"] != 'person':
                    checkAndCreateColumn(index, eachObject["name"])

            file_content = get_file(file_path=way2, as_png=False)
            image=iterm_show_file(way2, data=file_content, inline=True, height=None),
            
            filtered_data_cur = [item for item in detections if item['name'] == 'person']
            personCount = len(filtered_data_cur)

            if PrevDetection[index]:
                diffStat = compare_persons(PrevDetection[index], filtered_data_cur)
                if diffStat > 0:
                    statObj[index] *= (1 - (diffStat / personCount))

            if maxPerson[index] < personCount:
                maxPerson[index] = personCount

            total_time = time.time() - startPoint[index]
            if total_time > (60 * 5):  # every 5 minutes
                fixStatistic(index, maxPerson[index], statObj[index])
                startPoint[index] = time.time()
                maxPerson[index] = 0
                statObj[index] = 1

            PrevDetection[index] = detections

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

            





# Main function to initialize and start processing threads
def main():
    global access_token, listId, structable

    if not checkAndCreateList():
        print('checkAndCreateList - fail')
        exit()

    threads = []
    for rtsp_info in RTSP_URLS:
    
      thread = Thread(
            target=process_stream,
            args=(rtsp_info["name"], rtsp_info["url"], rtsp_info["weights"], rtsp_info["threshold"], "")
        )
      if False:  
       for d in range(rtsp_info["weights"]):
        thread = Thread(
            target=process_stream,
            args=(rtsp_info["name"], rtsp_info["url"], rtsp_info["weights"], rtsp_info["threshold"], d)
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()