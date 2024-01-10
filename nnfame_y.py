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


# os.environ['KMP_DUPLICATE_LIB_OK']='True'
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
# os.environ ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
# os.environ ["CUDA_VISIBLE_DEVICES"] = ""

class Response1:
    def __init__(self, code1, text1):
        self.result = code1
        self.text = text1


def fixStatistic():
    pass

def checkImg(pp=probaility,img1='',name1="image_1new"):
    start_time = time.time() 
    # predictions, probabilities = detector.classifyImage("./image1.jpg", result_count=20)
    
    detections = detector.detectObjectsFromImage(input_image=os.path.join(execution_path , "image1.jpg"), output_image_path=os.path.join(execution_path , "imagenew.jpg"), minimum_percentage_probability=30)

    end_time = time.time()  # время окончания выполнения
    execution_time = end_time - start_time  # вычисляем время выполнения
    print(f"- Время распознования: {execution_time} секунд")
    
    persomCount = 0
    for eachObject in detections:
        print(eachObject["name"] , " : ", eachObject["percentage_probability"], " : ", eachObject["box_points"] )
        if eachObject["name"]=='person':
            persomCount = 1+persomCount
        # print(eachObject["box_points"][0] )
        # print(eachObject["box_points"][1] )
        # print(eachObject["box_points"][2] )
        # print(eachObject["box_points"][3] )
        print("--------------------------------")
    
    if maxPerson<persomCount:
        maxPerson=persomCount
    
    total_time = startPoint - start_time 
    
    if total_time>(60*eachMin):
        fixStatistic()
        startPoint = time.time() 
        maxPerson = 0
        
        
    # for eachPrediction, eachProbability in zip(predictions, probabilities):
    #   if(probabilities[0]>0.3):
        # print(eachPrediction , " : " , eachProbability)
        
        
    # return detector.detectObjectsFromImage(
    # input_image=os.path.join(execution_path , img1), # "вхдное" изображения для распознования
    # output_image_path=os.path.join(execution_path , name1+now.strftime("%m_%d_%Y_%H_%M_%S")+".jpg"), # новое изображение которое является результатом обрабоки "входного изображения"
    # minimum_percentage_probability=pp
    # )
    
#get lists list
# curl 'https://domotel-admin.mobsted.ru/api/v8/lists?page=1&pageSize=100&appId=14' \
#create stat list
# curl 'https://domotel-admin.mobsted.ru/api/v8/lists' \
#   --data-raw 'AppId=14&name=statistic&description=stat+data+from+ours+camera&structure=%7B%22links%22%3A%5B%5D%2C%22tables%22%3A%5B%5D%7D' \
# adding table
# curl 'https://domotel-admin.mobsted.ru/api/v8/lists/12/newtable' \
#   --data-raw 'json=%5B%7B%22name%22%3A%22statofobjects%22%2C%22fields%22%3A%5B%5D%7D%5D' \
# curl 'https://domotel-admin.mobsted.ru/api/v8/lists/12/newtable' \
# --data-raw 'json=%5B%7B%22name%22%3A%22statofobjects%22%2C%22fields%22%3A%5B%7B%22name%22%3A%22date%22%2C%22type%22%3A%22timestamp+without+time+zone%22%7D%2C%7B%22name%22%3A%22time%22%2C%22type%22%3A%22text%22%7D%2C%7B%22name%22%3A%22person%22%2C%22type%22%3A%22text%22%7D%2C%7B%22name%22%3A%22personAvg%22%2C%22type%22%3A%22text%22%7D%5D%7D%5D' \
# new col
#   curl 'https://domotel-admin.mobsted.ru/api/v8/lists/12/newcolumn' \
# --data-raw 'tableName=statofobjects&json=%5B%7B%22name%22%3A%22date%22%2C%22type%22%3A%22timestamp+without+time+zone%22%7D%5D' \
# rem col
# curl 'https://domotel-admin.mobsted.ru/api/v8/lists/12/column?tableName=statofobjects&columnName=date' \
# curl 'https://domotel-admin.mobsted.ru/api/v8/lists/12/newtable' \
# --data-raw 'json=%5B%7B%22name%22%3A%22statofobjects%22%2C%22fields%22%3A%5B%7B%22name%22%3A%22date%22%2C%22type%22%3A%22timestamp+without+time+zone%22%7D%2C%7B%22name%22%3A%22time%22%2C%22type%22%3A%22text%22%7D%2C%7B%22name%22%3A%22person%22%2C%22type%22%3A%22text%22%7D%2C%7B%22name%22%3A%22personAvg%22%2C%22type%22%3A%22text%22%7D%5D%7D%5D' \

def simpleRequest(isGet = False, **params):
        try:
            if isGet:
                r = requests.get(**params)
            else:
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
        print('result:'+str(r.result))
        print('status_code:'+str(r.status_code))
        print('text:'+str(r.text)[0:2000])
        
        if r.status_code != 200:
            return False
        data = r.json()
        if not 'data' in data:
            print(' not data 0 ' + str(data))
            return False
        if not 'meta' in data:
            print(' not meta 0 ' + str(data))
            return False


        for dataList in data['data']:
            print(' data[data] ',dataList)
        
        return r

def getListId(access_token, tables):
    Headers = { 'Authorization' : "Bearer "+str(access_token) }
    
    listId = 0
    
    r = simpleRequest(isGet=True, url = urlD+url_l+"?page=1&pageSize=100&appId="+str(AppId), headers=Headers)
    data = r.json()

    for dataList in data['data']:
        print('dataList',dataList)
        print('dataList name',dataList['attributes']['name'])    
        print('dataList satatus',dataList['attributes']['status'])
        if dataList['attributes']['name']=='statistic':
            listId = dataList['attributes']['id']
            for table in dataList['attributes']['structure']['tables']:
                if table['name']=='statofobjects':
                    tables['statofobjects']=1
    return listId
                
def checkAndCreateList():
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

    tables = []
    listId = getListId(access_token,tables)
        
    if listId == 0 :
        # createList
        maindata = 'AppId='+str(AppId)+'&name=statistic&description=stat+data+from+ours+camera&structure=%7B%22links%22%3A%5B%5D%2C%22tables%22%3A%5B%5D%7D'
        r = simpleRequest(url=urlD+url_l, Headers=Headers, data=maindata)
        
    listId = getListId(access_token,tables)
    if listId == 0 :
        print(' List not created ' + str(urlD))
        return False

    if len(tables)==0:
        #createTable
        maindata = [{"name":"statofobjects","fields":[{"name":"date","type":"timestamp without time zone"},{"name":"time","type":"text"},{"name":"person","type":"text"},{"name":"personAvg","type":"text"}]}]
        r = simpleRequest(url=urlD+url_l, Headers=Headers, json=maindata)

    listId = getListId(access_token,tables)
    if len(tables)==0:
        print(' table not created ' + str(urlD))
        return False
    

            












if not checkAndCreateList():
    print('checkAndCreateList - fail')  
    return False

  
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

execution_path = os.getcwd()
print('execution_path',execution_path)
now = datetime.now()



eachMin = 5

startPoint = time.time() 
maxPerson = 0



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
