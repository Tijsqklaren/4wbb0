import GPIO
from imutils.video import VideoStream
import imagezmq
import socket
import speech_recognition as sr
import json
from threading import Thread
import time

def activateSpeech(){
    objectLabel = "bottle"

    sendQuery = {'type': 'objectLabel', 'value': objectLabel}

    mySocket.sendto(json.dumps(sendQuery),(SERVER_IP,PORT_NUMBER))

    activateSearch()
}

def powerOFF(){
    subprocess.call(['shutdown', '-h', 'now'], shell=False)
}

# Search for the object
def activateSearch(){
    # initiate a while loop
    beepGenerator.active = False

    t = Thread(target=beepGenerator)
    t.start()
    while True:
        # Get the frame and send it
        frame = vs.read()
        sender.send_image(rpiName, frame)

        # Receive data back from the server
        (data,addr) = mySocket.recvfrom(SIZE)
        data = data.decode('utf8', 'strict')
        if(len(data)):
            dataDict = json.loads(data)
            if(len(dataDict)):
                if(dataDict['type'] == "centerDiff"):
                    percentageValue = dataDict['value']
                    beepGenerator.active = True
                    frequency = percentageValue

        # If the object is found, quit the loop
        if GPIO.input(pins['finishPIN']) == GPIO.HIGH:
            break
        
}

# Beep generator
frequency = 1
def beepGenerator():
    while not beepGenerator.active:
        print(datetime.now(), 'start')
        time.sleep(1/frequency)
        print(datetime.now(), 'end')

# Init pins
pins = {'speechPIN': 0, 'powerPIN': 1, 'finishPIN': 2}
for pin in pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set op image socket
server_ip = "192.168.0.11"
sender = imagezmq.ImageSender(connect_to="tcp://{}:5555".format(server_ip))
rpiName = socket.gethostname()
vs = VideoStream(usePiCamera=False).start()
    
# Set event listeners
GPIO.add_event_detect(pins['speechPIN'], GPIO.FALLING, , callback=activateSpeech)
GPIO.add_event_detect(pins['powerPIN'], GPIO.FALLING, , callback=powerOFF)