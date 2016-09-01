import threading
import events
import picamera
import time
import os
import util

class MainThread(threading.Thread):
    """Template thread"""
    def __init__(self, configParser):
        threading.Thread.__init__(self)
        self.events = []
        self._stop = False
        self.eventWait = threading.Event()
        self.name = "IR Camera"
        print("Created new '{name}' thread".format(name = self.name))

        self.recording = False
        self.pirMotion = False
        self.thermalDetection = False
        self.camera = picamera.PiCamera()
        resX = int(configParser.get('ir_camera', 'res_x'))
        resY = int(configParser.get('ir_camera', 'res_y'))
        self.camera.resolution = (resX, resY)
        self.recordingData = {}
        self.videoData = {}
        self.startTime = time.time()

    def run(self):
        print("{name} thread running.".format(name = self.name))
        util.make_dirs(["./ir_videos"])
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
        elif self.event.type == events.PIR_MOTION_START:
            self.pir_motion_start()
        elif self.event.type == events.PIR_MOTION_END:
            self.pir_motion_end()
        elif self.event.type == events.THERMAL_DETECTION_START:
            self.thermal_detection_start()
        elif self.event.type == events.THERMAL_DETECTION_END:
            self.thermal_detection_end()
              
    def stop(self):
        print("Stopping '{name}'.".format(name = self.name))
        # Some 'final' things go here.
        self.camera.close()
        self._stop = True

    def start_recording(self):
        print("Starting recording.")
        self.recording = True
        self.startTime = time.time()
        self.recordingFolder = "./ir_videos/"+str(int(time.time()*1000))+".h264"
        self.camera.start_recording(self.recordingFolder)
        self.videoData = {
            "recordingDateTime": util.datetimestamp(),
            "startTimestamp": util.timestamp()
            }

    def stop_recording(self):
        print("Stopping recording.")
        self.recording = False
        
        self.videoData["duration"] = int(time.time()-self.startTime)
        self.recordingData["videoFile"] = self.videoData
        self.recordingData["__type__"] = "videoRecording"
        self.camera.stop_recording()
        util.save_data(self.recordingData, self.recordingFolder)
        self.recordingData = {}

    def pir_motion_start(self):
        self.pirMotion = True
        self.update_recording()

    def pir_motion_end(self):
        self.pirMotion = False
        self.update_recording()

    def thermal_detection_start(self):
        self.thermalDetection = True
        self.update_recording()

    def thermal_detection_end(self):
        self.thermalDetection = False
        self.update_recording()

    def update_recording(self):
        if self.recording:
            if not self.pirMotion and not self.thermalDetection:
                self.stop_recording()
        else:
            if self.pirMotion or self.thermalDetection:
                self.start_recording()
