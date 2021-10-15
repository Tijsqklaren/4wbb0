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

# Set variables
imagePort = 5555
dataPort = 8000
SIZE = 1024
serverConfigured = False
percentageValue = False

def activateSpeech(self):
    objectLabel = "bottle"

    sendQuery = {'type': 'objectLabel', 'value': objectLabel}

    mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))

    activateSearch()

def powerOFF(self):
    print('powering device off')

    # Tell the server to also terminate the connection
    sendQuery = {'type': 'clientPowerOff', 'value': True}
    mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))

    # Actually shut down
    subprocess.call(['sudo', 'shutdown', '-h', 'now'], shell=False)

# Search for the object
def activateSearch():
<<<<<<< master
    # initiate a while loop

    buzzerThread = Thread(target=beepGenerator)
    buzzerThread.start()
=======
    beepGenerator.active = False

    beepGeneratorThread = Thread(target=beepGenerator)
    beepGeneratorThread.start()

    getDiffThread = Thread(target=getDiff)
    getDiffThread.start()
>>>>>>> local
    vs = VideoStream(usePiCamera=False).start()

    while True:
        # Get the frame and send it
        frame = vs.read()
        sender.send_image(rpiName, frame)

        # If the object is found, quit the loop
        if GPIO.input(buttonPins['finishPIN']) == GPIO.LOW:
            print('Quit button pressed')
            sendQuery = {'type': 'searchFinished', 'value': True}
            mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))
            beepGenerator.active = False

            vs.stream.release()
            break

# Beep generator
frequencyRange = [1, 100]
def beepGenerator():
<<<<<<< master
    while beepGenerator.active:
        print('start')
        time.sleep(1/frequency)
        print('end')                
=======
    global percentageValue
    while beepGenerator.active:
        if percentageValue > 0:
            # Lower percentages -> frequency closer to upper part of range, higher percentage -> frequency closer to lower part of range
            frequencyRange = frequencyRange[0] + (frequencyRange[1]-frequencyRange[0]) * (1-abs(percentageValue)/100)
            # Start buzzer
            GPIO.output(buzzerPin, GPIO.HIGH)
            time.sleep(1/(2*frequency))
            # Stop buzzer
            GPIO.output(buzzerPin, GPIO.LOW)
            time.sleep(1/(2*frequency))
>>>>>>> local

# Listen to input from server
def socketThreadFunc():
    while True:
        # Receive data back from the server
        (data,addr) = mySocket.recvfrom(SIZE)
        data = data.decode('utf8', 'strict')
        if(len(data)):
            dataDict = json.loads(data)
            if(len(dataDict)):
<<<<<<< master
                if(dataDict['type'] == "localizationStart"):
                    print('Start pinging for device')
                elif(dataDict['type'] == "localizationEnd"):
                    print('Stop pinging for device')
                elif(dataDict['type'] == "centerDiff"):
=======
                if(dataDict['type'] == "centerDiff"):
                    print('object found')
                    global percentageValue
>>>>>>> local
                    percentageValue = dataDict['value']
                    beepGenerator.active = True

def initSockets():
    # Set op image socket
    hostName = gethostbyname('0.0.0.0')

    mySocket = socket(AF_INET, SOCK_DGRAM)
    mySocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    mySocket.bind((hostName, dataPort))

    print("Waiting for server's connection")
    (data,addr) = mySocket.recvfrom(SIZE)
    data = data.decode('utf8', 'strict')
    if(len(data)):
        dataDict = json.loads(data)
        if(len(dataDict)):
            if(dataDict['type'] == "serverHandshake"):
                server_ip = dataDict['server_ip']
                
                sendQuery = {'type': 'clientHandshake', 'value': True}
                mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))

                print("Server connected on " + server_ip)
                
                sender = imagezmq.ImageSender(connect_to="tcp://{ip}:{port}".format(ip = server_ip, port = dataPort))
                rpiName = gethostbyname('0.0.0.0')
                serverConfigured = True

# Init pins
# Set GPIO mode to board (thus using the printed numbering on the pi)
GPIO.setmode(GPIO.BOARD)
<<<<<<< master
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
=======
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
    
# Set event listeners
while True:
    if serverConfigured:
        if GPIO.input(buttonPins['speechPIN']) == GPIO.LOW:
            activateSpeech(True)
        if GPIO.input(buttonPins['powerPIN']) == GPIO.LOW:
            powerOFF(True)
    else:
        initSockets()
>>>>>>> local
