import threading
import events
import time
from pylepton import Lepton
import cv2
import numpy as np
import os
import util
import shutil

imageDelay = 0.2    # delay between images in seconds
newImageEvent = threading.Event()
thermalDetection = False
sensitivity = 50
bufferSize = 20
latestImage = None
allImagesFolder = "./thermalData"
captureTimeRange = False
startCaptureTime = '00:00'
stopCaptureTime = '00:00'

class MainThread(threading.Thread):
    """Theramla camera main therad. Starts and controls child threads that
       capture thermal images, process image and render images."""
    def __init__(self, configParser):
        threading.Thread.__init__(self)
        self.events = []
        self._stop = False
        self.eventWait = threading.Event()
        self.name = "Thermal Camera"
        self.recording = False
        print("Created new '{name}' thread".format(name = self.name))

        self.renderThreads = []
        sensitivity = int(configParser.get('thermal_camera', 'sensitivity'))
        bufferSize = int(configParser.get('thermal_camera', 'buffer_size'))
        global captureTimeRange
        captureTimeRange |= configParser.get('thermal_camera', 'capture_time_range') == "True"
        global startCaptureTime
        startCaptureTime = configParser.get('thermal_camera', 'start_capture_time')
        global stopCaptureTime
        stopCaptureTime = configParser.get('thermal_camera', 'stop_capture_time')

    def run(self):
        print("{name} thread running.".format(name = self.name))
        # Starting thread to take images and thead to detect things in images
        self.cameraThread = CameraThread()
        self.picDetection = PicDetection()
        self.cameraThread.start()
        self.picDetection.start()
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
        #print(events.THERMAL_DETECTION_END)
        if self.event == None:
            print("Error: self.event is not set when trying to run event...")
        elif self.event.type == events.STOP:
            self.stop()
        elif self.event.type == events.THERMAL_DETECTION_START:
            self.thermal_detection_start()
        elif self.event.type == events.THERMAL_DETECTION_END:
            self.thermal_detection_end()

    def stop(self):
        print("Stopping '{name}'.".format(name = self.name))
        self.picDetection.stop()
        self.picDetection.join()
        self.cameraThread.stop()
        self.cameraThread.join()
        self._stop = True

    def thermal_detection_start(self):
        self.cameraThread.start_recording()
        self.data = {
            "__type__": "thermalVideoRecording",
            "recordingDateTime": util.datetimestamp(),
            "recordingTime": util.timestamp()
            }

    def thermal_detection_end(self):
        images = self.cameraThread.stop_recording()
        self.data["duration"] = len(images)/5
        render = RenderAndUpload(images, self.data)
        render.start()

class CameraThread(threading.Thread):
    """Takes thermal pictures setting the new image event each time an image
       is taken."""
    def __init__(self):
        threading.Thread.__init__(self)
        self._stop = False
        self.lastImageCaptureTime = None
        self.images = []    # List of images
        self.recording = False
        
    def run(self):
        with Lepton() as self.l:
            while not self._stop:
                time.sleep(self.time_to_next_image())
                self.take_image()
        print("Thermal capture thread stopped")

    def stop(self):
        print("Stopping thermal camera capture thread.")
        self._stop = True

    def time_to_next_image(self):
        """Returns the time in seconds intil the next image should be taken"""
        if self.lastImageCaptureTime == None:
            ttni = 0
        else:
            ttni = self.lastImageCaptureTime - time.time() + imageDelay
            if ttni < 0:
                ttni = 0
        self.lastImageCaptureTime = time.time()
        return ttni

    def take_image(self):
        global latestImage
        a,_ = self.l.capture()
        cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX)
        np.right_shift(a, 8, a)
        
        if not self.recording:
            while len(self.images) > 5:
                del self.images[0]

        self.images.append(a)
        latestImage = a
        newImageEvent.set()

    def start_recording(self):
        self.recording = True

    def stop_recording(self):
        self.recording = False
        i = self.images
        self.images = []
        return i

class PicDetection(threading.Thread):
    """Loops through waiting for a new image event and processing the image to
       see if something is in the image. If so a global event is set"""
    def __init__(self):
        threading.Thread.__init__(self)
        self._stop = False
        self.image = None
        self.noDetectionCountdown = 0
        self.recording = False

    def run(self):
        while not self._stop:
            newImageEvent.wait()
            newImageEvent.clear()
            if latestImage != None and not self._stop:
                self.image = latestImage
                self.detection()
        print("Stopped thermal image render therad.")

    def stop(self):
        print("Stopping thermal image render therad.")
        self._stop = True
        newImageEvent.set()

    def detection(self):
        global thermalDetection
        detect = self.image_detection()
        if detect:
            self.noDetectionCountdown = bufferSize
        else:
            self.noDetectionCountdown -= 1
        if not thermalDetection and self.noDetectionCountdown > 0:
            events.new_event(events.THERMAL_DETECTION_START)
            thermalDetection = True
        elif thermalDetection and self.noDetectionCountdown <= 0:
            thermalDetection = False
            events.new_event(events.THERMAL_DETECTION_END)

    def image_detection(self):
        if captureTimeRange and not util.inTimeRange(startCaptureTime, stopCaptureTime):
            print("Not in time range")
            return False        
        maxVal = self.image.max()
        minVal = self.image.min()
        top25 = maxVal-(maxVal-minVal)*1/4
        numInTop25 = 0
        total = 0
        for x in range(0, len(self.image)):
            for y in range(0, len(self.image[x])):
                total += 1
                if self.image[x][y] >= top25:
                    numInTop25 += 1 
        m = numInTop25 < sensitivity
        return m

class RenderAndUpload(threading.Thread):
    """Takes array of images, saves to images then renders images into an avi, then sends for uploading."""
    def __init__(self, images, data):
        threading.Thread.__init__(self)
        self.images = images
        self.data = data

    def run(self):

        # Craete folder to save images in
        imagesFolder = os.path.join(allImagesFolder, (str(int(time.time())))+util.rand_str())
        os.makedirs(imagesFolder)
        # Save images
        imageIndex = 0
        for i in self.images:
            imageName = str(imageIndex).zfill(6) + '.jpg'
            imageIndex += 1
            cv2.imwrite(os.path.join(imagesFolder, imageName), np.uint8(i))

        # Render into avi
        inputF = os.path.join(imagesFolder, "%06d.jpg")
        outputF = os.path.join(imagesFolder, "file.avi")
        command = "/usr/local/bin/ffmpeg -r 5 -i {i} {o}".format(
            i = inputF, o = outputF)
        print(command)
        os.system(command)
        util.save_data(self.data, outputF)
        shutil.rmtree(imagesFolder)
