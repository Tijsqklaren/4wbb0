from threading import Thread
import time
from datetime import datetime

frequency = 1

# Frequencygenerator of beeps
def beepGenerator():
    while not beepGenerator.cancelled:
        print(datetime.now(), 'start')
        time.sleep(1/frequency)
        print(datetime.now(), 'end')

beepGenerator.cancelled = False

t = Thread(target=beepGenerator)
t.start()

while True:
    frequencyInput = int(input("frequency: "))
    if isinstance(frequencyInput, int):
        frequency = frequencyInput

# beepGenerator.cancelled = True