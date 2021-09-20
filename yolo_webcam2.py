import cv2
import numpy as np
import argparse
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


def draw_prediction(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
    label = str(classes[class_id])

    color = COLORS[class_id]

    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)

    cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

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
# set height
video_capture.set(4, 416)

while video_capture.isOpened():
    # Capture frame-by-frame
    ret, image = video_capture.read()
    Width = image.shape[1]
    Height = image.shape[0]
    scale = 0.00392

    blob = cv2.dnn.blobFromImage(image, scale, (416, 416), (0, 0, 0), True, crop=False)

    net.setInput(blob)

    outs = net.forward(get_output_layers(net))

    class_ids = []
    confidences = []
    boxes = []
    conf_threshold = 0.5
    nms_threshold = 0.4

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * Width)
                center_y = int(detection[1] * Height)
                w = int(detection[2] * Width)
                h = int(detection[3] * Height)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])

    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    for i in indices:
        i = i[0]
        box = boxes[i]
        x = box[0]
        y = box[1]
        w = box[2]
        h = box[3]
        draw_prediction(image, class_ids[i], confidences[i], round(x), round(y), round(x + w), round(y + h))

    font = cv2.FONT_HERSHEY_SIMPLEX
    bottomLeftCornerOfText = (10, 200)
    fontScale = 1
    fontColor = (255, 255, 255)
    lineType = 2
    class_list = [i[0] for i in indices]

    ## Create a video capture object, in this case we are using the webcam
    if(video_capture.isOpened() == False):
        print("Error opening the webcam")
    ##Read fps and frame count
    else:
        ## Get frame rate information
        fps = video_capture.get(5)
        print("Frame Count : ", fps, "FPS")

    if ret:
        cv2.imshow("object detection", image)







    if cv2.waitKey(1) & 0xFF == ord('q'):
        video_capture.release()
        cv2.destroyAllWindows()
        break