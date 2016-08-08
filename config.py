import os

# Folders
dataFolder = '~/.data'
toUpload = os.path.join(dataFolder, 'to_upload')
uploaded = os.path.join(dataFolder, 'uploaded')
thermalFolder = os.path.join(dataFolder, 'thermal')
thermalImagesFolder = os.path.join(thermalFolder, 'images')
irVideoFolder = os.path.join(dataFolder, 'ir_video')
folderList = [
    dataFolder,
    toUpload,
    uploaded,
    thermalFolder,
    thermalImagesFolder,
    irVideoFolder
]

server = {
    "url": "http://52.62.79.0:8888"
}

irVideo = {
    "recordingLedPin": 12,
    "pirPin": 5,
    "timeout": 5
}

thermalVideo = {
    "bufferSize": 5,
    "timeout": 5,
    "sensitivity": 50,
    "fps": 5
}
