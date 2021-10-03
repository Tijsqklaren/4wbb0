import cv2
import numpy as np
import os
print('click "q" to quit')

# path to the files
configInput = os.path.abspath("./yolov3.cfg")
weightsInput = os.path.abspath("./yolov3.weights")
classesInput = os.path.abspath("./yolov3.txt")


def get_output_layers(net):
    layer_names = net.getLayerNames()

    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    return output_layers

# read in the class definitions
classes = None
with open(classesInput, 'r') as f:
    classes = [line.strip() for line in f.readlines()]

COLORS = np.random.uniform(0, 255, size=(len(classes), 3))

# setup the network
net = cv2.dnn.readNet(weightsInput, configInput)

video_capture = cv2.VideoCapture(0)
# set width
video_capture.set(3, 416)
video_capture.set(4, 416)

# Get the height of the video capture
ret, image = video_capture.read()
Width = image.shape[1]
Height = image.shape[0]
scale = 0.00392

# Some stylings
font = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (10, 200)
fontScale = 1
fontColor = (255, 255, 255)
lineType = 2

captureNr = 0

while video_capture.isOpened():
    fps = video_capture.get(5)
    print("Frame Count : ", fps, "FPS")
    
    # Capture frame-by-frame
    ret, image = video_capture.read()
    captureNr += 1
    print('Capture number: ' + str(captureNr))

    blob = cv2.dnn.blobFromImage(image, scale, (416, 416), (0, 0, 0), True, crop=False)

    net.setInput(blob)

    print('Started identifying')
    outs = net.forward(get_output_layers(net))
    print('Ended identifying')

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * Width)
                center_y = int(detection[1] * Height)
                print(str(classes[class_id]))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        video_capture.release()