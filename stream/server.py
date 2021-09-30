import imagezmq
import cv2
import os
import numpy as np

configInput = os.path.abspath("./yolov3.cfg")
weightsInput = os.path.abspath("./yolov3.weights")
classesInput = os.path.abspath("./yolov3.txt")

imageHub = imagezmq.ImageHub()


#read in the class definitions
classes = None
with open(classesInput, 'r') as f:
    classes = [line.strip() for line in f.readlines()]

COLORS = np.random.uniform(0, 255, size=(len(classes), 3))


#setup the network
net = cv2.dnn.readNet(weightsInput, configInput)



while True:
    (rpiName, frame) = imageHub.recv_image()
    imageHub.send_reply(b'OK')
    cv2.imshow('Input', frame)

    c = cv2.waitKey(1)
    if c == 27:
        break

cv2.destroyAllWindows()