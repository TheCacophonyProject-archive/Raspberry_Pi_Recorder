import threading
import events

class MainThread(threading.Thread):
    """Template thread"""
    def __init__(self):
        threading.Thread.__init__(self)
        self.events = []
        self._stop = False
        self.eventWait = threading.Event()
        self.name = "Template thraed."
        print("Created new '{name}' thread".format(name = self.name))

    def run(self):
        print("{name} thread running.".format(name = self.name))
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
        # Some 'final' things go here.
        self._stop = True
