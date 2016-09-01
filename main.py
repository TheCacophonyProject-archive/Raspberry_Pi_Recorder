import sys
from CacophonyModules import pir, ir_camera, events, thermal_camera, upload
import RPi.GPIO as GPIO
import ConfigParser
import os
import time

# Get config file
configParser = ConfigParser.RawConfigParser()
configPath = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "config.txt")
if not os.path.isfile(configPath):
    print("Can't find config file: " + configPath)
    while True:
        time.sleep(1)
configParser.read(configPath)

stop = False
threads = []
# Add threads to list
threads.append(pir.MainThread())
threads.append(ir_camera.MainThread(configParser))
threads.append(thermal_camera.MainThread())
threads.append(upload.MainThread(configParser))
# Start all threads
for thread in threads:
    thread.start()

try:
    while not stop:
        events.eventWait.wait(1000)
        if len(events.eventQueue):
            event = events.eventQueue[0]
            del events.eventQueue[0]
            for thread in threads:  # Send event to each thread.
                thread.new_event(event)
            if not len(events.eventQueue):
                events.eventWait.clear() # Clears eventWait if there are no more events
except KeyboardInterrupt:
    print("Keyboard Interrupt.")
except:
    e = sys.exc_info()[0]
    print("Exception: " + str(e))
finally:
    print("Stopping threads.")
    # Calling threads to stop
    for thread in threads:
        thread.new_event(events.get_stop_event())
    # Waiting for threads to stop
    for thread in threads:
        thread.join()
    GPIO.cleanup()
    print("End.")
