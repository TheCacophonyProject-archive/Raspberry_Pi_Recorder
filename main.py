import time
import multiprocessing
import RPi.GPIO as GPIO

import util
import ir_recorder
import thermal_recorder
import config



def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(5, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(6, GPIO.OUT, initial = GPIO.LOW)
    GPIO.output(6, GPIO.HIGH)
    GPIO.output(6, GPIO.LOW)
    if not util.make_dirs(config.folderList):
        print("Failed to make folders for data..")
        return False


setup()
print("Waiting for button press.")
GPIO.wait_for_edge(5, GPIO.RISING)


print("Starting in...")
x = 5
while x > 0:
    print(x)
    time.sleep(1)
    x -= 1
print("Starting...")

GPIO.output(6, GPIO.HIGH)
time.sleep(2)

ir_recorder.init()
util.upload_update()

jobs = []
p = multiprocessing.Process(target=ir_recorder.run())
p.start()
jobs.append(p)
p = multiprocessing.Process(target=thermal_recorder.run())
p.start()
jobs.append(p)

while True:
    time.sleep(0.1)
