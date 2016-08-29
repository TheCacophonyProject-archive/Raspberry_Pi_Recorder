import threading
import time

PIR_MOTION_START = "PIR motion detection started."
PIR_MOTION_END = "PIR motion detection ended."
THERMAL_DETECTION_START = "Theraml motion detection started."
THERMAL_DETECTION_END = "Thermal motion detection ended."
IR_RECORDING_START = "IR camera started recording."
IR_RECORDING_END = "IR camera finished recording."
THERAML_RECORDING_START = "Theraml camera started recording."
THERAML_RECORDING_END = "Theraml camera finished recording."
STOP = "Exit event."
PAUSE = "Pause event."
DATA_TO_UPLOAD = "Some data to upload to the server"

eventQueue = []     # List of events that have occured, events are removed from this list as the main thread runs them.
eventWait = threading.Event()   # Main thread will wait for this to be set before checking for new events.

class Event():
    """Object describing an event that has occured, used for threads to comunitace to each other."""
    def __init__(self, eType, extra):
        self.type = eType
        self.extra = extra
        self.time = time.time()
        print("New event created. {}".format(self))
        #save and log event

    def __str__(self):
        return ("Type: {}, Extra: {}, Time: {}".format(
            self.type,
            self.extra,
            self.time))

def new_event(eType = None, extra = {}, datetime = None):
    """Created a new Event Object, adds it to the list of events and then sets
        the eventWait."""
    # TODO: Check if valid data
    if not datetime:
        datetime = "123"    # TODO: get datetime function

    newEvent = Event(eType, extra)
    eventQueue.append(newEvent)
    eventWait.set()

def get_stop_event():
    return Event(STOP, {}) # Event that when sent to a thread the thread should exit.
