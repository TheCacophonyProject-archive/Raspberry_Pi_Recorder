import sys
from CacophonyModules import pir, ir_camera, events, thermal_camera, upload
import RPi.GPIO as GPIO


stop = False
threads = []
# Add threads to list
threads.append(pir.MainThread())
threads.append(ir_camera.MainThread())
threads.append(thermal_camera.MainThread())
threads.append(upload.MainThread())
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
