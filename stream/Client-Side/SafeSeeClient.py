import RPi.GPIO as GPIO
from imutils.video import VideoStream
import imagezmq
import socket
from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM
import speech_recognition as sr
import json
from threading import Thread
import time
import sys
import subprocess

def activateSpeech(self):
    objectLabel = "bottle"

    sendQuery = {'type': 'objectLabel', 'value': objectLabel}

    mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))

    activateSearch()

def powerOFF(self):
    print('power off')
    subprocess.call(['sudo', 'shutdown', '-h', 'now'], shell=False)

# Search for the object
def activateSearch():
    # initiate a while loop

    buzzerThread = Thread(target=beepGenerator)
    buzzerThread.start()
    vs = VideoStream(usePiCamera=False).start()

    while True:
        # Get the frame and send it
        frame = vs.read()
        sender.send_image(rpiName, frame)

        # If the object is found, quit the loop
        if GPIO.input(pins['finishPIN']) == GPIO.LOW:
            print('Quit button pressed')
            sendQuery = {'type': 'searchFinished', 'value': True}
            mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))
            beepGenerator.active = False

            vs.stream.release()
            break

# Beep generator
frequency = 1
def beepGenerator():
    while beepGenerator.active:
        print('start')
        time.sleep(1/frequency)
        print('end')                

# Listen to input from server
def socketThreadFunc():
    while True:
        # Receive data back from the server
        (data,addr) = mySocket.recvfrom(SIZE)
        data = data.decode('utf8', 'strict')
        if(len(data)):
            dataDict = json.loads(data)
            if(len(dataDict)):
                if(dataDict['type'] == "localizationStart"):
                    print('Start pinging for device')
                elif(dataDict['type'] == "localizationEnd"):
                    print('Stop pinging for device')
                elif(dataDict['type'] == "centerDiff"):
                    percentageValue = dataDict['value']
                    beepGenerator.active = True
                    print(percentageValue)

# Init pins
GPIO.setmode(GPIO.BOARD)
pins = {'speechPIN': 8, 'powerPIN': 5, 'finishPIN': 10}
for pin in pins:
    GPIO.setup(pins[pin], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Stay in loop, until server has given his IP
while True:
    (data,addr) = mySocket.recvfrom(SIZE)
    data = data.decode('utf8', 'strict')
    if(len(data)):
        dataDict = json.loads(data)
        if(len(dataDict)):
            if(dataDict['type'] == "serverData"):
                if(len(dataDict['server_ip'])):
                    server_ip = dataDict['server_ip']
                    sendQuery = {'type': 'serverDataReceived', 'value': True}
                    mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))
                    print("Received server's IP: " + server_ip)
                    break

# Set up sockets
hostName = gethostbyname('0.0.0.0')
imagePort = 5555
dataPort = 5000
SIZE = 1024

# Connect socket for images
sender = imagezmq.ImageSender(connect_to="tcp://{}:5555".format(server_ip))
rpiName = gethostbyname('0.0.0.0')

# Connect socket for data
mySocket = socket(AF_INET, SOCK_DGRAM)
mySocket.bind((hostName, dataPort))

# Listen for localization signal
socketThread = Thread(target=socketThreadFunc)
socketThread.start()

# Listen to buttons
while True:
    print('Started listening for input from buttons')
    if GPIO.input(pins['speechPIN']) == GPIO.LOW:
        activateSpeech(True)
    if GPIO.input(pins['powerPIN']) == GPIO.LOW:
        powerOFF(True)