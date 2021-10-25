import imagezmq
import cv2

imageHub = imagezmq.ImageHub()

while True:
    (rpiName, frame) = imageHub.recv_image()
    imageHub.send_reply(b'OK')
    cv2.imshow('Input', frame)

    c = cv2.waitKey(1)
    if c == 27:
        break

cv2.destroyAllWindows()