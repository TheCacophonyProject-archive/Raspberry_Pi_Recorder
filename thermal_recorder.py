import time
import RPi.GPIO as GPIO
import numpy as np
import cv2
from pylepton import Lepton
import os
import subprocess

import util
import config


images = []
nextImageCaptureTime = None

renderImages = {}
imagesFolder = None
imageIndex = 1

renderProcess = None
rendering = ""

bufferSize = config.thermalVideo['bufferSize']
allImagesFolder = config.thermalImagesFolder
timeout = config.thermalVideo['timeout']
fps  = config.thermalVideo['fps']
sensitivity = config.thermalVideo['sensitivity']

def update_image_capture(l):
    wait_for_next_image()
    image = get_image(l)
    images.append(image)
    while len(images) > bufferSize:
        del images[0]
    if motion(image):
        motion_detected(l)

def get_image(l):
    a,_ = l.capture()
    cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX)
    np.right_shift(a, 8, a)
    return a

def save_images(images):
    global imageIndex
    global imagesFolder
    if imagesFolder == None:
        imagesFolder = os.path.join(allImagesFolder, (str(int(time.time()))))
        imageIndex = 1
        if not os.path.exists(imagesFolder):
            os.makedirs(imagesFolder)
    for i in images:
        imageName = str(imageIndex).zfill(6) + '.jpg'
        cv2.imwrite(os.path.join(imagesFolder, imageName), np.uint8(i))
        imageIndex += 1

def motion_detected(l):
    global imagesFolder
    save_images(images)
    x = timeout
    total = 1
    startTime = util.timestamp()
    recordingDatetime = util.datetimestamp()
    while x > 0:
        print('Thermal motion detected')
        x -= 1
        total += 1
        wait_for_next_image()
        image = get_image(l)
        save_images([image])
        if motion(image):
            x = timeout
    videoFileMetadata = {
        "duration": total/fps,
        "startTimestamp": startTime,
        "recordingDateTime": recordingDatetime
    }
    metadata = {
        "__type__": "videoRecording",
        "videoFile": videoFileMetadata
    }

    renderImages[imagesFolder] = metadata
    imagesFolder = None

def wait_for_next_image():
    global nextImageCaptureTime
    if time.time() > nextImageCaptureTime:
        print("Too fast!!")
    while time.time() < nextImageCaptureTime:
        time.sleep(0.01)
    nextImageCaptureTime = time.time() + 1.0/fps

def motion(image):
    maxVal = image.max()
    minVal = image.min()
    top25 = maxVal-(maxVal-minVal)*1/4
    numInTop25 = 0
    total = 0
    for x in range(0, len(image)):
        for y in range(0, len(image[x])):
            total += 1
            if image[x][y] >= top25:
                numInTop25 += 1
    #print("Top 25: {}".format(numInTop25))
    m = (numInTop25 < sensitivity)
    return m

def update_render():
    global renderProcess
    global rendering
    global rendered
    global renderingData
    if renderProcess == None and len(renderImages) > 0:
        rendering = list(renderImages.keys())[0]
        renderingData = renderImages[rendering]
        del renderImages[rendering]
        images = os.path.join(rendering, "%06d.jpg")
        output = os.path.join(rendering, "file.avi")
        args = ['ffmpeg', '-r', str(fps), '-i', images, output]
        renderProcess = subprocess.Popen(args)
    if renderProcess != None and renderProcess.poll() == 0:
        renderProcess = None
        print("finished render")
        util.save_data(renderingData, os.path.join(rendering, 'file.avi'))
        util.upload_update()
        
def run():
    with Lepton() as l:
        while True:
            update_image_capture(l)
            update_render()
            
