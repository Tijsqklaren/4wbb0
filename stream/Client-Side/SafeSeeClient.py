import RPi.GPIO as GPIO
from imutils.video import VideoStream
import imagezmq
import socket
from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR
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
    # beepGenerator.active = False

    # t = Thread(target=beepGenerator)
    # t.start()

    getDiffThread = Thread(target=getDiff)
    getDiffThread.start()
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

            vs.stream.release()
            break

# Beep generator
frequency = 1
def beepGenerator():
    while not beepGenerator.active:
        print('start')
        time.sleep(1/frequency)
        print('end')

# read from server
def getDiff():
    while True:
        # Receive data back from the server
        (data,addr) = mySocket.recvfrom(SIZE)
        data = data.decode('utf8', 'strict')
        if(len(data)):
            dataDict = json.loads(data)
            if(len(dataDict)):
                if(dataDict['type'] == "centerDiff"):
                    print('object found')
                    percentageValue = dataDict['value']
                    beepGenerator.active = True
                    print(percentageValue)

# Init pins
GPIO.setmode(GPIO.BOARD)
pins = {'speechPIN': 8, 'powerPIN': 5, 'finishPIN': 10}
for pin in pins:
    GPIO.setup(pins[pin], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set op image socket
server_ip = "192.168.0.22"
hostName = gethostbyname('0.0.0.0')
imagePort = 5555
dataPort = 8000
SIZE = 1024

sender = imagezmq.ImageSender(connect_to="tcp://{}:5555".format(server_ip))
rpiName = gethostbyname('0.0.0.0')

mySocket = socket(AF_INET, SOCK_DGRAM)
mySocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
mySocket.bind((hostName, dataPort))
    
# Set event listeners
# GPIO.add_event_detect(pins['speechPIN'], GPIO.FALLING, callback=activateSpeech)
# GPIO.add_event_detect(pins['powerPIN'], GPIO.FALLING, callback=powerOFF)

while True:
    if GPIO.input(pins['speechPIN']) == GPIO.LOW:
        activateSpeech(True)
    if GPIO.input(pins['powerPIN']) == GPIO.LOW:
        powerOFF(True)