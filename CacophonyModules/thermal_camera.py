import threading
import events
import time
from pylepton import Lepton
import cv2
import numpy as np
import os

imageDelay = 0.2    # delay between images in seconds
newImageEvent = threading.Event()
images = []
thermalDetection = False
sensitivity = 50

class MainThread(threading.Thread):
    """Theramla camera main therad. Starts and controls child threads that
       capture thermal images, process image and render images."""
    def __init__(self):
        threading.Thread.__init__(self)
        self.events = []
        self._stop = False
        self.eventWait = threading.Event()
        self.name = "Thermal Camera"
        print("Created new '{name}' thread".format(name = self.name))

        self.renderThreads = []

    def run(self):
        print("{name} thread running.".format(name = self.name))
        # Starting thread to take images and thead to detect things in images
        self.cameraThread = cameraThread()
        self.picDetection = picDetection()
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
        if self.event == None:
            print("Error: self.event is not set when trying to run event...")
        elif self.event.type == events.STOP:
            self.stop()

    def stop(self):
        print("Stopping '{name}'.".format(name = self.name))
        self.picDetection.stop()
        self.picDetection.join()
        self.cameraThread.stop()
        self.cameraThread.join()
        self._stop = True

class cameraThread(threading.Thread):
    """Takes thermal pictures setting the new image event each time an image
       is taken. Also saving the images if the thermal camera is recording."""
    def __init__(self):
        threading.Thread.__init__(self)
        self._stop = False
        self.lastImageCaptureTime = None
        
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
        if self.lastImageCaptureTime == None:
            ttni = 0
        else:
            ttni = self.lastImageCaptureTime - time.time() + imageDelay
            if ttni < 0:
                ttni = 0
        self.lastImageCaptureTime = time.time()
        return ttni

    def take_image(self):
        a,_ = self.l.capture()
        cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX)
        np.right_shift(a, 8, a)
        while len(images) > 5:
            del images[0]
        images.append(a)
        newImageEvent.set()
        

class picDetection(threading.Thread):
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
            if len(images) and not self._stop:
                self.image = images[0]
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
            self.noDetectionCountdown = 20
        else:
            self.noDetectionCountdown -= 1
        if not thermalDetection and self.noDetectionCountdown > 0:
            events.new_event(events.THERMAL_DETECTION_START)
            thermalDetection = True
        elif thermalDetection and self.noDetectionCountdown <= 0:
            thermalDetection = False
            events.new_event(events.THERMAL_DETECTION_END)

    def image_detection(self):
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

# Old code that was used to save images and convert them into a video when the
# thermal camera was ran in a differnt process, now using threads instead.
# Just here as a reminder.

##def save_images(images):
##    global imageIndex
##    global imagesFolder
##    if imagesFolder == None:
##        imagesFolder = os.path.join(allImagesFolder, (str(int(time.time())))+util.rand_str())
##        imageIndex = 1
##        if not os.path.exists(imagesFolder):
##            os.makedirs(imagesFolder)
##    for i in images:
##        imageName = str(imageIndex).zfill(6) + '.jpg'
##        cv2.imwrite(os.path.join(imagesFolder, imageName), np.uint8(i))
##        imageIndex += 1

##def update_render():
##    global renderProcess
##    global rendering
##    global rendered
##    global renderingData
##    if renderProcess == None and len(renderImages) > 0:
##        rendering = list(renderImages.keys())[0]
##        print(rendering)
##        renderingData = renderImages[rendering]
##        del renderImages[rendering]
##        images = os.path.join(rendering, "%06d.jpg")
##        output = os.path.join(rendering, "file.avi")
##        print(images)
##        print(output)
##        args = ['/usr/local/bin/ffmpeg', '-r', str(fps), '-i', images, output]
##        renderProcess = subprocess.Popen(args)
##    if renderProcess != None and renderProcess.poll() == 0:
##        renderProcess = None
##        print("finished render")
##        util.save_data(renderingData, os.path.join(rendering, 'file.avi'))
##        util.upload_update()

