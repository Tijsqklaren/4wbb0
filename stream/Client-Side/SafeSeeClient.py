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
import pyaudio
import wave

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
recognizerListening = False
recording = True

# Audio recording
FORMAT = pyaudio.paInt16
CHANNELS = 1
device_info = sd.query_devices(0, 'input')
RATE = int(device_info['default_samplerate'])

class VideoCapture:
    def __init__(self, name):
        self.cap = cv2.VideoCapture(name)
        self.q = queue.Queue()
        t = Thread(target=self._reader)
        t.daemon = True
        t.start()

    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        return self.q.get()

    def release(self):
        self.cap.release()

def activateSpeech():
    global recording
    global mySocket
    global server_ip
    global dataPort

    sendQuery = {'type': 'startSpeech'}
    mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))

    print("Start recording")

    fileName = "outputfile.wav"

    wf = wave.open(fileName, 'wb')
    wf.setnchannels(CHANNELS)
    
    p = pyaudio.PyAudio()
    
    stream = p.open(format=FORMAT,
					channels=CHANNELS,
					rate=RATE,
					input=True,
					frames_per_buffer=SIZE)
    
    frames = []
    
    print('start listening')
    n = 0
    while recording:
        print('listening')
        n += 1
        data = stream.read(SIZE)
        frames.append(data)

    print("Quit recording")
        
    sample_width = p.get_sample_size(FORMAT)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    sendQuery = {'type': 'quitSpeech', 'size': n, 'sample_width': sample_width, 'rate': RATE}
    mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))

    file = open(fileName, "rb")
    SendData = file.read(1024)

    i = 0
    while i <= n:
        i += 1
        mySocket.sendto(SendData,(server_ip,dataPort))
        SendData = file.read(1024)

    print("All data sent")

def powerOFF(self):
    global mySocket
    print('powering device off')

    # Tell the server to also terminate the connection
    sendQuery = {'type': 'clientPowerOff', 'value': True}
    mySocket.sendto(str.encode(json.dumps(sendQuery)),(server_ip,dataPort))
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

    cam = VideoCapture(0)

    sender = imagezmq.ImageSender(connect_to="tcp://{ip}:{port}".format(ip = server_ip, port = imagePort))

    print('Start searching')

    while True:
        # Get the frame and send it
        frame = cam.read()
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

    frequencyRange = [1, 20]

    while True:
        if beepGeneratorActive:
            # Lower percentages -> frequency closer to upper part of range, higher percentage -> frequency closer to lower part of range
            frequency = frequencyRange[0] + (frequencyRange[1]-frequencyRange[0]) * (1-abs(percentageValue)/100)
            # print('frequency: ' + str(round(frequency, 2)) + "Hz")
            # print('percentage: ' + str(round(percentageValue, 2)) + '%')
            # print((frequencyRange[1]-frequencyRange[0]) * (1-abs(percentageValue)/100))
            # Start buzzer
            GPIO.output(buzzerPin, GPIO.HIGH)
            time.sleep(0.05)
            # Stop buzzer
            GPIO.output(buzzerPin, GPIO.LOW)
            time.sleep(1/frequency)

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
                elif dataDict['type'] == "objectLabelIdentified":
                    activateSearchThread = Thread(target=activateSearch)
                    activateSearchThread.start()
                elif dataDict['type'] == "noObjectFound":
                    beepGeneratorActive = False

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

def recCallback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

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
    
# Set event listeners
print('Started listening to buttons')
while True:
    if serverConfigured:
        if GPIO.input(buttonPins['speechPIN']) == GPIO.LOW and not recognizerListening:
            print("starting activation of speech")
            speechThread = Thread(target=activateSpeech)
            speechThread.start()
            recording = True
            recognizerListening = True
        if GPIO.input(buttonPins['speechPIN']) == GPIO.HIGH and recognizerListening:
            print("quiting of speech")
            recording = False
            recognizerListening = False
        if GPIO.input(buttonPins['powerPIN']) == GPIO.LOW:
            powerOFF(True)
    else:
        initSockets()