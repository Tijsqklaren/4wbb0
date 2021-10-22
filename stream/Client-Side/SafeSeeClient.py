import RPi.GPIO as GPIO
import imagezmq
import socket
from socket import socket, gethostbyname, gethostname, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR
import json
from threading import Thread
import time
import sys
import cv2
import subprocess
import os
import queue
import sounddevice as sd
import vosk

# Set variables
imagePort = 5555
dataPort = 5000
SIZE = 1024
serverConfigured = False
percentageValue = False
beepGeneratorActive = False
speechPinDown = False
rpiName = gethostname()
recognizedLabel = ""

def activateSpeech():
    global recognizerListening

    recognizerListening = True

def terminateSpeech():
    global mySocket
    global server_ip
    global dataPort
    global objectLabel
    global recognizerListening
    global recognizedLabel

    recognizerListening = False

    recognizedLabel

    with open('../../yolov3.txt') as f:
    if recognizedLabel in f.read():
        objectLabel = recognizedLabel

    print('Searching for: ' + objectLabel)

    sendQuery = {'type': 'objectLabel', 'value': objectLabel}

    mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))

def powerOFF(self):
    global mySocket
    print('powering device off')

    # Tell the server to also terminate the connection
    sendQuery = {'type': 'clientPowerOff', 'value': True}
    mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))

    # Actually shut down
    subprocess.call(['sudo', 'shutdown', '-h', 'now'], shell=False)

# Search for the object
def activateSearch():
    global mySocket
    global beepGeneratorActive
    global buzzerThread
    global rpiName
    global imagePort
    global server_ip

    buzzerThread = Thread(target=beepGenerator)
    buzzerThread.start()
    beepGeneratorActive = False

    cam = cv2.VideoCapture(0)

    sender = imagezmq.ImageSender(connect_to="tcp://{ip}:{port}".format(ip = server_ip, port = imagePort))

    print('Start searching')

    while True:
        # Get the frame and send it
        rval, frame = cam.read()
        
        sender.send_image(rpiName, frame)

        # If the object is found, quit the loop
        if GPIO.input(buttonPins['finishPIN']) == GPIO.LOW:
            print('Quit button pressed')
            sendQuery = {'type': 'searchFinished', 'value': True}
            mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))
            beepGeneratorActive = False
           
            cam.release()
            break

# Beep generator
def beepGenerator():
    global percentageValue
    global beepGeneratorActive

    frequencyRange = [1, 100]

    while True:
        if beepGeneratorActive:
            # Lower percentages -> frequency closer to upper part of range, higher percentage -> frequency closer to lower part of range
            frequency = frequencyRange[0] + (frequencyRange[1]-frequencyRange[0]) * (1-abs(percentageValue)/100)
            print('frequency: ' + str(round(frequency, 2)) + "Hz")
            print('percentage: ' + str(round(percentageValue, 2)) + '%')
            # print((frequencyRange[1]-frequencyRange[0]) * (1-abs(percentageValue)/100))
            # Start buzzer
            GPIO.output(buzzerPin, GPIO.HIGH)
            time.sleep(1/(2*frequency))
            # Stop buzzer
            GPIO.output(buzzerPin, GPIO.LOW)
            time.sleep(1/(2*frequency))

# Listen to input from server
def socketThreadFunc():
    global mySocket
    global SIZE
    global beepGeneratorActive
    global percentageValue

    while True:
        # Receive data back from the server
        (data,addr) = mySocket.recvfrom(SIZE)
        data = data.decode('utf8', 'strict')
        if(len(data)):
            dataDict = json.loads(data)
            if(len(dataDict)):
                if(dataDict['type'] == "localizationStart"):
                    print('Start pinging for device')
                    GPIO.output(buzzerPin, GPIO.HIGH)
                elif(dataDict['type'] == "localizationEnd"):
                    print('Stop pinging for device')
                    GPIO.output(buzzerPin, GPIO.LOW)
                elif(dataDict['type'] == "centerDiff"):
                    percentageValue = dataDict['value']
                    beepGeneratorActive = True
                elif dataDict['type'] == "objectLabelReceived":
                    activateSearchThread = Thread(target=activateSearch)
                    activateSearchThread.start()

def initSockets():
    global mySocket
    global SIZE
    global server_ip
    global dataPort
    global imagePort
    global serverConfigured
    global socketThread

    # Set op image socket
    hostName = gethostbyname('0.0.0.0')

    mySocket = socket(AF_INET, SOCK_DGRAM)
    mySocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    mySocket.bind((hostName, dataPort))

    print("Waiting for server's connection")
    (data,addr) = mySocket.recvfrom(SIZE)
    data = data.decode('utf8', 'strict')
    # data = json.dumps({"type": "serverHandshake", "server_ip": "192.168.2.124"})
    if(len(data)):
        dataDict = json.loads(data)
        if(len(dataDict)):
            if(dataDict['type'] == "serverHandshake"):
                server_ip = dataDict['server_ip']
                
                sendQuery = {'type': 'clientHandshake', 'value': True}
                mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))

                print("Server connected on " + server_ip)
                
                serverConfigured = True

                socketThread = Thread(target=socketThreadFunc)
                socketThread.start()

                voiceRecThread = Thread(target=voiceRecognizer)
                voiceRecThread.start()

def recCallback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def voiceRecognizer():
    global model
    global q
    global recognizerListening
    global recognizedLabel

    samplerate = 
    device = 

    while True:
        if recognizerListening:
            with sd.RawInputStream(samplerate=samplerate, blocksize = 8000, device=device, dtype='int16',
                                    channels=1, callback=recCallback):

                rec = vosk.KaldiRecognizer(model, samplerate)
                while recognizerListening:
                    data = q.get()
                    if rec.AcceptWaveform(data):
                        recognizedLabel = rec.Result()
                        print(rec.Result())
                    else:
                        recognizedLabel = rec.PartialResult()
                        print(rec.PartialResult())

# Init pins
# Set GPIO mode to board (thus using the printed numbering on the pi)
GPIO.setmode(GPIO.BOARD)
# Name the pins used for buttons
buttonPins = {'speechPIN': 8, 'powerPIN': 5, 'finishPIN': 10}
# Loop through the buttons to setup
for pin in buttonPins:
    GPIO.setup(buttonPins[pin], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Setup the buzzer pin
buzzerPin = 12
GPIO.setup(buzzerPin, GPIO.OUT)

# Run the function to initialize the sockets
initSockets()

# Initialize the voice recognition model
model = vosk.Model(args.model)
q = queue.Queue()
    
# Set event listeners
while True:
    if serverConfigured:
        if GPIO.input(buttonPins['speechPIN']) == GPIO.LOW:
            activateSpeech()
        if GPIO.input(buttonPins['speechPIN']) == GPIO.HIGH and recognizerListening:
            terminateSpeech()
        if GPIO.input(buttonPins['powerPIN']) == GPIO.LOW:
            powerOFF(True)
    else:
        initSockets()