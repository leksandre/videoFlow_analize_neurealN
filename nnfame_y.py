import cv2
import sys
import m3u8
import tkinter as tk
import numpy as np
from PIL import Image
import os
from datetime import datetime
import random
import time
from some import API_KEY, pgdb, pguser, pgpswd, pghost, pgport, pgschema, url_a, url_l, urlD, log_e, pass_e, managers_chats_id, service_chats_id, AppId
import requests
import json




# config 
execution_path = os.getcwd()

print('1')
# from imageai.Detection import ObjectDetection
# detector = ObjectDetection()

# from imageai.Classification import ImageClassification
# detector = ImageClassification()

from imageai.Detection import ObjectDetection
detector = ObjectDetection()
print('2')

probaility = 30

global lastImg
lastImg = ''
global maxPerson
maxPerson = 0
global statObj
statObj = 1
global startPoint
startPoint = time.time() 
global PrevDetection
PrevDetection = False
global structable
structable = False
global listId
listId = 0
global newCols
newCols = []
global access_token
access_token = ''


execution_path = os.getcwd()
print('execution_path',execution_path)
now = datetime.now()



eachMin = 5.0





# os.environ['KMP_DUPLICATE_LIB_OK']='True'
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
# os.environ ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
# os.environ ["CUDA_VISIBLE_DEVICES"] = ""


#comments 


    # for eachPrediction, eachProbability in zip(predictions, probabilities):
    #   if(probabilities[0]>0.3):
        # print(eachPrediction , " : " , eachProbability)
        
    # return detector.detectObjectsFromImage(
    # input_image=os.path.join(execution_path , img1), # "вхдное" изображения для распознования
    # output_image_path=os.path.join(execution_path , name1+now.strftime("%m_%d_%Y_%H_%M_%S")+".jpg"), # новое изображение которое является результатом обрабоки "входного изображения"
    # minimum_percentage_probability=pp
    # )
    
#get lists list
# curl 'https://h1.h2/api/v8/lists?page=1&pageSize=100&appId=14' \
#create stat list
# curl 'https://h1.h2/api/v8/lists' \
#   --data-raw 'AppId=14&name=statistic&description=stat+data+from+ours+camera&structure=%7B%22links%22%3A%5B%5D%2C%22tables%22%3A%5B%5D%7D' \
# adding table
# curl 'https://h1.h2/api/v8/lists/12/newtable' \
#   --data-raw 'json=%5B%7B%22name%22%3A%22statofobjects%22%2C%22fields%22%3A%5B%5D%7D%5D' \
# curl 'https://h1.h2/api/v8/lists/12/newtable' \
# --data-raw 'json=%5B%7B%22name%22%3A%22statofobjects%22%2C%22fields%22%3A%5B%7B%22name%22%3A%22date%22%2C%22type%22%3A%22timestext%22%7D%2C%7B%22name%22%3A%22time%22%2C%22type%22%3A%22text%22%7D%2C%7B%22name%22%3A%22person%22%2C%22type%22%3A%22text%22%7D%2C%7B%22name%22%3A%22person_avg%22%2C%22type%22%3A%22text%22%7D%5D%7D%5D' \
# new col
#   curl 'https://h1.h2/api/v8/lists/12/newcolumn' \
# --data-raw 'tableName=statofobjects&json=%5B%7B%22name%22%3A%22date%22%2C%22type%22%3A%22timestext%22%7D%5D' \
# rem col
# curl 'https://h1.h2/api/v8/lists/12/column?tableName=statofobjects&columnName=date' \
# curl 'https://h1.h2/api/v8/lists/12/newtable' \
# --data-raw 'json=%5B%7B%22name%22%3A%22statofobjects%22%2C%22fields%22%3A%5B%7B%22name%22%3A%22date%22%2C%22type%22%3A%22timestext%22%7D%2C%7B%22name%22%3A%22time%22%2C%22type%22%3A%22text%22%7D%2C%7B%22name%22%3A%22person%22%2C%22type%22%3A%22text%22%7D%2C%7B%22name%22%3A%22person_avg%22%2C%22type%22%3A%22text%22%7D%5D%7D%5D' \

# add row
# curl 'https://h1.h2/api/v8/list' \
#   --data-raw 'listId=16&tableName=statofobjects&json=%7B%22date%22%3Anull%2C%22time%22%3A%22datetime1%22%2C%22person%22%3A%2212%22%2C%22person_avg%22%3A%220.8%22%7D' \
#   --compressed

# class adn func


class Response1:
    def __init__(self, code1, text1):
        self.result = code1
        self.text = text1

def checkAndCreateColumn(nameCol):
    if not structable:
        print(f"'это не то': {structable}")
        return
    if not isinstance(structable, list):
        print(f"'это не лист': {structable}")
        return 
    colNameExist = False
    colAvgExist = False
    for col in structable:
        if col['name']==nameCol:
            colNameExist = True
        if col['name']==nameCol+'_avg':
            colAvgExist = True
    Headers = { 'Authorization' : "Bearer "+str(access_token), 'Content-Type': 'application/x-www-form-urlencoded' }
    # if not colAvgExist:
    #     # listId = getListId() #get from global
    #     maindata = f"tableName=statofobjects&json=%5B%7B%22name%22%3A%22{nameCol+'_avg'}%22%2C%22type%22%3A%22text%22%7D%5D"
    #     r = simpleRequest(url=urlD+url_l+'/'+str(listId)+'/newcolumn', headers=Headers, data=maindata)
    if not colNameExist:
        # listId = getListId() #get from global
        maindata = f"tableName=statofobjects&json=%5B%7B%22name%22%3A%22{nameCol}%22%2C%22type%22%3A%22text%22%7D%5D"
        r = simpleRequest(url=urlD+url_l+'/'+str(listId)+'/newcolumn', headers=Headers, data=maindata)
    getListId()
    
def fixStatistic(*params):
    # print(f"fix stats {params}")
    # print(f"fix stats params 0 {params[0]}")
    # print(f"fix stats params 1 {params[1]}")
    Headers = { 'Authorization' : "Bearer "+str(access_token), 'Content-Type': 'application/x-www-form-urlencoded' }
    if 1:
        # listId = getListId() #get from global
        now_1 = datetime.now() 
        time_1 = now_1.strftime("%H:%M:%S")
        date_1 = now_1.strftime("%Y-%m-%d")
        # date_1 = now_1.strftime("%d/%m/%Y %H:%M")
        maindata = f"listId={listId}&tableName=statofobjects&json=%7B%22date%22%3A%22{date_1}%22%2C%22time%22%3A%22{time_1}%22%2C%22person%22%3A%22{params[0]}%22%2C%22person_avg%22%3A%22{params[1]}%22%7D"
        print(f"fix stats maindata: {maindata}")
        r = simpleRequest(url=urlD+(url_l[:-1]), headers=Headers, data=maindata, showresp = True)
    pass

def compare_detections(list1, list2, path=""):
    if path=="": #если это "нулевой" уровень
        stat1 = 0 
    # Проверяем, являются ли оба объекта списками
    if isinstance(list1, list) and isinstance(list2, list):
        # Проверяем, имеют ли списки одинаковую длину
        if len(list1) != len(list2):
            print(f"Различное количество элементов: {path}")
        # Рекурсивно сравниваем каждый элемент списков
        for i in range(min(len(list1), len(list2))):
            res = compare_detections(list1[i], list2[i], f"{path}[{i}]")
            if path=="": #если это "нулевой" уроыень
                if res:
                    pass
                else:
                    stat1 = stat1+1
            else:
                return res
    else:
        # Если объекты не являются списками, сравниваем их значения
        if list1 != list2:
            print(f"Объект переместился: {path} - {list1}, {list2}")
            return True
        print(f"Объект не двигается: {path} - {list1}, {list2}")
        return False
    if path=="": #если это "нулевой" уровень
        print(f"Объектов без движения: {stat1}")

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
                  stat1 = stat1+1
    print(f"Объектов без движения: {stat1}")
    return stat1
        
def checkImg(pp=probaility,img1='',name1="image_1new"):
    
    global maxPerson
    global statObj
    global startPoint
    global PrevDetection
    
    start_time = time.time() 
    # predictions, probabilities = detector.classifyImage("./image1.jpg", result_count=20)
    
    detections = detector.detectObjectsFromImage(input_image=os.path.join(execution_path , "image1.jpg"), output_image_path=os.path.join(execution_path , "imagenew.jpg"), minimum_percentage_probability=30)

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

            



if not checkAndCreateList():
    print('checkAndCreateList - fail')  
    exit()


# detector.setModelTypeAsRetinaNet()
# detector.setModelPath( os.path.join(execution_path , "resnet50_coco_best_v2.1.0.h5"))

# detector.setModelTypeAsResNet50()
# detector.setModelPath('/home/Aleksandr/nnstream/resnet50-19c8e357.pth')

detector.setModelTypeAsYOLOv3()
detector.setModelPath( os.path.join(execution_path , "yolov3.pt"))

detector.loadModel()



VIDEO_URL = "https://hd-auth.skylinewebcams.com/live.m3u8?a=u1913k4vhn0ss7r5cnuf03th91"

cam = cv2.VideoCapture(VIDEO_URL)
while 1:
    total_frames = cam.get(1)

    cam.set(1, 10)
    ret, frame = cam.read()
    cv2.imwrite('./image1.jpg', frame)

    playlist = m3u8.load(VIDEO_URL)  # this could also be an absolute filename
    #print(playlist.segments)
    #print(playlist.target_duration)
    for a_number in [1]:
        number_str = str(a_number)
        zero_filled_number = number_str#.zfill(5)
        print(zero_filled_number)
        img1 = r"./image"+str(zero_filled_number)+".jpg"
        img2 = r"./image"+str(zero_filled_number)+".jpg"

        if not os.path.isfile(img1):
            print('error file',img1)
            continue
        if not os.path.isfile(img2):
            print('error file',img2)
            continue

        # image = Image.open(img1)
        # new_image = image.resize((640, 512))
        # img1 = "_tmp_.jpg"
        # new_image.save(img1)

        # указываем необходимые для распознования классы объектов на тепловом и обычном изображениях
        # custom = detector.CustomObjects(car=True, motorcycle=True,  bus=True,   truck=True)
        rgb_array = []
        detections = checkImg(probaility,img1,str(zero_filled_number)+"image_1new_")

        # print("result image")
        # for eachObject in detections:
        #     print(eachObject["name"] , " : ", eachObject["percentage_probability"])
        #     b = eachObject["detection_details"]
        #     print(("x1:"+str(b[0]), "y1:"+str(b[1])), ("x2:"+str(b[2]), "y2:"+str(b[3])))
        #     rgb_array.append(b)
