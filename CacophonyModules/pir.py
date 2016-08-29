import threading
import events
import RPi.GPIO as GPIO
import time

pirPin = 5

class MainThread(threading.Thread):
    """Template thread"""
    def __init__(self):
        threading.Thread.__init__(self)
        self.events = []
        self._stop = False
        self.eventWait = threading.Event()
        self.name = "PIR"
        print("Created new '{name}' thread".format(name = self.name))

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pirPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

    def run(self):
        print("{name} thread running.".format(name = self.name))
        GPIO.add_event_detect(
            pirPin,
            GPIO.FALLING,
            callback = self.motion_callback,
            bouncetime = 200)
        while not self._stop:
            self.eventWait.wait()
            self.event = self.events[0]
            del self.events[0]
            self.run_event()
            if not len(self.events):
                self.eventWait.clear()
        print("'{name}' stopped.".format(name = self.name))

    def new_event(self, event):
        self.events.append(event)
        self.eventWait.set()

    def run_event(self):
        if self.event == None:
            print("Error: self.event is not set when trying to run event...")
        elif self.event.type == events.STOP:
            self.stop()

    def stop(self):
        print("Stopping '{name}'.".format(name = self.name))
        GPIO.remove_event_detect(pirPin)
        self._stop = True
        

    def motion_callback(self, channel):
        if GPIO.input(pirPin):  # Pir inactive
            return
        events.new_event(eType = events.PIR_MOTION_START, extra = "cat123")
        motionTime = time.time()
        while time.time() < motionTime + 10:
            if not GPIO.input(pirPin): # PIR active
                motionTime = time.time()
            time.sleep(0.5)
        events.new_event(eType = events.PIR_MOTION_END, extra = "cat321")
    
