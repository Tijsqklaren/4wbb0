import imagezmq
import cv2
import os
import numpy as np
from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM, gethostname
import json
from threading import Thread
import time
from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import wave

# Set files for object recognition
configInput = os.path.abspath("./yolov3.cfg")
weightsInput = os.path.abspath("./yolov3.weights")
classesInput = os.path.abspath("./yolov3.txt")

# variables
lostObjectLabel = ""
terminateSearch = False

dataPort = 5000
imagePort = 5555
SIZE = 1024

loopbreak = False


def get_output_layers(net):
    layer_names = net.getLayerNames()

    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    return output_layers

def draw_prediction(img, class_id, confidence, x, y, x_plus_w, y_plus_h, d_center_x, d_center_y):
    global objectColor
    global otherObjectsColor

    if str(classes[class_id]) == lostObjectLabel:
        color = objectColor
    else:
        color = otherObjectsColor

    label = str(classes[class_id])

    center_x = round((x_plus_w-x)/2+x)
    center_y = round((y_plus_h-y)/2+y)

    # Rectangle around complete object
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)

    # Circle in center of object
    cv2.circle(img, (center_x,center_y), 10, (0, 0, 255), 0)

    # Put text on top
    cv2.putText(img, (label + ' ' + str(d_center_x) + '% ' + str(d_center_y) + '%'), (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

def listenForInput():
    global mySocket
    global terminateSearch
    global lostObjectLabel
    global client_ip
    global dataPort
    global lostObjectLabel

    while True:
        (data,addr) = mySocket.recvfrom(SIZE)
        receivedData = data.decode('utf8', 'strict')
        if len(receivedData):
            dataDict = json.loads(receivedData)
            if dataDict['type'] == "searchFinished":
                terminateSearch = True
            elif dataDict['type'] == "clientPowerOff":
                print('Client is powering off, so turn server off')
                loopbreak = True
            elif dataDict['type'] == "startSpeech":
                print("Voice recording started")

                (data,addr) = mySocket.recvfrom(SIZE)
                receivedData = data.decode('utf8', 'strict')
                if len(receivedData):
                    dataDict = json.loads(receivedData)
                    if dataDict['type'] == "quitSpeech":
                        fileSize = dataDict['size']
                        sample_width = dataDict['sample_width']
                        RATE = dataDict['rate']

                        print("Voce recording quit, filesize: " + str(fileSize))

                        frames = []
                        
                        i = 0
                        while i <= fileSize:
                            i += 1
                            (RecvData, addr) = mySocket.recvfrom(SIZE)
                            # file.write(RecvData)
                            frames.append(RecvData)
                            print(i, i<=fileSize)

                        file = wave.open("recv.wav", 'wb')

                        file.setnchannels(1)
                        file.setsampwidth(sample_width)
                        file.setframerate(RATE)
                        file.writeframes(b''.join(frames))
                        file.close()

                        print("Written to file")

                wf = wave.open(os.path.abspath("./recv.wav"), "rb")
                rec = KaldiRecognizer(model, wf.getframerate())

                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        rec.Result()
                    else:
                        rec.PartialResult()

                spokenWord = json.loads(rec.FinalResult())['text']
                print(spokenWord)

                with open(classesInput, 'r') as f:
                    if spokenWord in f.read():
                        print("Searching for: " + spokenWord)
                        lostObjectLabel = spokenWord
                        mySocket.sendto(str.encode(json.dumps({"type": "objectLabelIdentified", "value": spokenWord})),(client_ip,dataPort))
                        terminateSearch = False
            
def initSockets():
    global mySocket
    global server_ip
    global client_ip
    global dataPort
    global SIZE
    global imageHub

    # Initialize sockets
    imageHub = imagezmq.ImageHub()
    hostName = gethostbyname('0.0.0.0')

    client_ip = "192.168.0.10"
    # server_ip = gethostbyname(gethostname())
    server_ip = "192.168.0.26"

    mySocket = socket(AF_INET, SOCK_DGRAM)
    mySocket.bind((hostName, dataPort))

    print('Sockets started, waiting for confirmation from client')

    # Send the server's IP-addres
    mySocket.sendto(str.encode(json.dumps({"type": "serverHandshake", "server_ip": server_ip})),(client_ip,dataPort))

    # Wait for confirmation from client
    (data,addr) = mySocket.recvfrom(SIZE)
    receivedData = data.decode('utf8', 'strict')

    if len(receivedData):
        dataDict = json.loads(receivedData)
        if(dataDict['type'] == "clientHandshake"):
            serverConfigured = True
            print('Client confirmed connection')
            listenForInputThread = Thread(target=listenForInput)
            listenForInputThread.start()

#read in the class definitions
classes = None
with open(classesInput, 'r') as f:
    classes = [line.strip() for line in f.readlines()]


#setup the deep neural network
net = cv2.dnn.readNet(weightsInput, configInput)

# Some styling
font = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (10, 200)
fontScale = 1
objectColor = (255, 0, 0)
otherObjectsColor = (0,0,0)
lineType = 2

# Run the function to initialize the sockets
initSockets()

# Initialize model
print(os.path.abspath("./stream/Server-Side/model_large"))
model = Model(os.path.abspath("./stream/Server-Side/model_large"))

while True:
    if cv2.waitKey(1) & 0xFF == ord('q') or loopbreak:
        imageHub.close()
        cv2.destroyAllWindows()
        break

    if terminateSearch:
        print('Terminated search')
        lostObjectLabel == ""
        cv2.destroyAllWindows()

    while not len(lostObjectLabel):
        continue

    (rpiName, frame) = imageHub.recv_image()
    imageHub.send_reply(b'OK')
    
    Width = frame.shape[1]
    Height = frame.shape[0]

    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop = False)

    net.setInput(blob)

    outs = net.forward(get_output_layers(net))

    class_ids = []
    confidences = []
    boxes = []
    conf_threshold = 0.5
    nms_threshold = 0.4

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * Width)
                center_y = int(detection[1] * Height)
                w = int(detection[2] * Width)
                h = int(detection[3] * Height)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])

                # Compute percentage from centerpoint
                d_center_x = round(((2*center_x)/Width - 1)*100)
                d_center_y = round((1 - (2*center_y)/Height)*100)

                if str(classes[class_id]) == lostObjectLabel:
                    mySocket.sendto(str.encode(json.dumps({"type": "centerDiff", "value": d_center_x})),(client_ip,dataPort))

    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    for i in indices:
        i = i[0]
        box = boxes[i]
        x = box[0]
        y = box[1]
        w = box[2]
        h = box[3]
        draw_prediction(frame, class_ids[i], confidences[i], round(x), round(y), round(x + w), round(y + h), d_center_x, d_center_y)

    class_list = [i[0] for i in indices]

    cv2.imshow('Input', frame)