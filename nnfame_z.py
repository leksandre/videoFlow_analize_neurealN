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
from some import API_KEY, pgdb, pguser, pgpswd, pghost, pgport, pgschema, url_e, url_c, log_e, pass_e, managers_chats_id, service_chats_id
import requests
# os.environ['KMP_DUPLICATE_LIB_OK']='True'
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
# os.environ ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
# os.environ ["CUDA_VISIBLE_DEVICES"] = ""

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


# detector.setModelTypeAsRetinaNet()
# detector.setModelPath( os.path.join(execution_path , "resnet50_coco_best_v2.1.0.h5"))

# detector.setModelTypeAsResNet50()
# detector.setModelPath('/home/Aleksandr/nnstream/resnet50-19c8e357.pth')

detector.setModelTypeAsYOLOv3()
detector.setModelPath( os.path.join(execution_path , "yolov3.pt"))

detector.loadModel()

def checkImg(pp=probaility,img1='',name1="image_1new"):
    start_time = time.time() 
    # predictions, probabilities = detector.classifyImage("./image1.jpg", result_count=20)
    
    detections = detector.detectObjectsFromImage(input_image=os.path.join(execution_path , "image1.jpg"), output_image_path=os.path.join(execution_path , "imagenew.jpg"), minimum_percentage_probability=30)

    end_time = time.time()  # время окончания выполнения
    execution_time = end_time - start_time  # вычисляем время выполнения
    print(f"- Время распознования: {execution_time} секунд")
    
    for eachObject in detections:
        print(eachObject["name"] , " : ", eachObject["percentage_probability"], " : ", eachObject["box_points"] )
        print("--------------------------------")
    
    # for eachPrediction, eachProbability in zip(predictions, probabilities):
    #   if(probabilities[0]>0.3):
        # print(eachPrediction , " : " , eachProbability)
        
        
    # return detector.detectObjectsFromImage(
    # input_image=os.path.join(execution_path , img1), # "вхдное" изображения для распознования
    # output_image_path=os.path.join(execution_path , name1+now.strftime("%m_%d_%Y_%H_%M_%S")+".jpg"), # новое изображение которое является результатом обрабоки "входного изображения"
    # minimum_percentage_probability=pp
    # )

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
