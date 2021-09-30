# import the necessary packages
from imutils.video import VideoStream
import imagezmq
import socket
import time

server_ip = "192.168.0.11"

sender = imagezmq.ImageSender(connect_to="tcp://{}:5555".format(server_ip))


rpiName = socket.gethostname()
vs = VideoStream(usePiCamera=False).start()

time.sleep(2.0)
 
while True:
    frame = vs.read()
    sender.send_image(rpiName, frame)