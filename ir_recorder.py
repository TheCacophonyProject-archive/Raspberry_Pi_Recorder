import time
import RPi.GPIO as GPIO
import picamera
import sys
import os

import util
import config

camera = picamera.PiCamera()
camera.resolution = (400, 300)
preview = False

pirPin = config.irVideo['pirPin']
recordingPin = config.irVideo['recordingLedPin']
timeout = config.irVideo['timeout']

irVideoFolder = config.irVideoFolder 

def init():
    print("Initialising IR recorder.")
    GPIO.setup(recordingPin, GPIO.OUT, initial = GPIO.LOW)
    GPIO.setup(pirPin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    
def run():
    startTime = util.datetimestamp(time.localtime())
    print("IR recorder startimg at {time}.".format(time = startTime))
    print("Timeout: {timeout}".format(timeout = timeout))
    GPIO.add_event_detect(
        pirPin,
        GPIO.RISING,
        callback = motion_callback,
        bouncetime=200)
    
def motion_callback(channel):
    """ This function should be called when the PIR detects a new movement. """
    # Getting metadata for recording.
    recordingDateTime = util.datetimestamp()
    startTimestamp = util.timestamp()
    startTime = time.time()
    print("Movement at time {time}".format(time = recordingDateTime))
    print("Starting recording....")

    # Get recording.
    recordingPath = start_recording()
    recording_wait()
    print("Stopping recording.")
    stop_recording()

    # Getting some more metadata.
    stopTime = time.time()
    duration = stopTime - startTime
    print("Recording went for {dur} seconds.".format(dur = duration))

    # Save metadata in dictionary.
    videoFileData = {
        'duration': duration,
        'startTimestamp': startTimestamp,
        'recordingDateTime': recordingDateTime
    }
    data = {
        '__type__': 'videoRecording',
        "videoFile": videoFileData
    }

    # Save recording and update upload.
    util.save_data(data, recordingPath)
    util.upload_update()
    
def save_recording(data):
    # Metadata as params
    # Makes a json from file and data.
    # saves the recording metadata as a json file in toupload file along with the recording.
    
    recordingName = data['recordingDateTime']+'.json'
    videoFileMetadata = {'duration': data['duration'],
                         'startTimestamp': data['startTimestamp'],
                         'recordingDateTime': data['recordingDateTime']}
    metadata = {'videoFile': videoFileMetadata}
    with open(toUpload+"/"+recordingName, 'w') as f:
        json.dump(metadata, f)


def recording_wait():
    detectTime = time.time()
    while detectTime + timeout > time.time():
        time.sleep(0.5)
        if GPIO.input(pirPin) == 1:
            print("Motion detected.")
            detectTime = time.time()

def start_recording():
    """ Starts a video recording, return the recording path. """
    recordingPath = os.path.join(irVideoFolder, util.datetimestamp() + ".h264")
    #GPIO.output(ledPin, GPIO.LOW)
    print(camera)
    camera.start_recording(recordingPath)
    if preview:
        camera.start_preview()
    return recordingPath

def stop_recording():
    #GPIO.output(ledPin, GPIO.HIGH)
    camera.stop_recording()
    if preview:
        camera.stop_preview()
    



