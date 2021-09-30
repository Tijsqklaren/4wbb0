import GPIO
from imutils.video import VideoStream
import imagezmq
import socket
import speech_recognition as sr

def activateSpeech(){
    
}

def powerOFF(){
    subprocess.call(['shutdown', '-h', 'now'], shell=False)
}

def activateSearch(){
    while True:
        frame = vs.read()
        sender.send_image(rpiName, frame)
        if GPIO.input(pins['finishPIN']) == GPIO.HIGH:
            break
        
}

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