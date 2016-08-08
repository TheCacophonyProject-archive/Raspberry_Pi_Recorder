import random
import string
import os
import time
import json
import thread
import shutil
import requests

import config

dataFolder = config.dataFolder
toUpload = config.toUpload
serverUrl = config.server['url']

uploadingList = []

def make_dirs(dirs):
    """Makes the dirs in the list given"""
    try:
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
    except OSError as e:
        print e
        return False        
    return True

def save_data(data, f):
    """ Saves the data and recording in the toUpload folder. """
    """ data shoud be a dictionary including __type__ (video, sound...). """
    """ f should be the file path. """

    # Make folder where the data and file will be saved.
    folder = os.path.join(toUpload, data['videoFile']['recordingDateTime']+'_'+ rand_str())
    if not make_dirs([folder]):
        print('Error with making folder when saving data: '+folder)
        return False

    # Move recording file into the folder made above.
    _, ext = os.path.splitext(f)
    os.rename(f, os.path.join(folder, 'file'+ext))

    # Save data as a json file into the folder made above.
    with open(os.path.join(folder, 'metadata.json'), 'w') as jsonFile:
        json.dump(data, jsonFile)

def upload_update():
    print("Checking for data to upload...")
    # Exit if allready uploading data.
    if (len(uploadingList) > 0):
        print("Already uploading data.")
        return
    dataFolders = [f for f in os.listdir(toUpload) if os.path.isdir(os.path.join(toUpload, f))]
    for dataFolder in dataFolders:
        if dataFolder not in uploadingList:
            print("Uploading data in folder {}".format(dataFolder))
            folderPath = os.path.join(toUpload, dataFolder)
            uploadingList.append(folderPath)
            thread.start_new_thread(upload, (folderPath,))
            return

def upload(dataFolder):
    """ Uploads data in the data flder. """
    # Load json and file.
    metadata = {}
    dataType = None
    files = {}
    for f in os.listdir(dataFolder):
        name, ext = os.path.splitext(f)
        if name == 'metadata' and ext == '.json':
            # Load metadata and find data type.
            metadataFile = open(os.path.join(dataFolder, f))
            metadata = json.loads(''.join(metadataFile.readlines()))
            dataType = metadata['__type__']
            del metadata['__type__']
        elif name == 'file':
            # Load data file.
            files['file'] = open(os.path.join(dataFolder, f))
        else:
            print("Error, unknown file in folder: " + f)

    # Get URL to post to.
    if dataType == 'videoRecording':
        url = serverUrl + '/api/v1/videoRecordings'
    else:
        print('Datatype "{}" unknown.'.format(dataType))
        return

    # Post and print status code.
    print('Posting data...')
    r = requests.post(url, files = files, data = {'data': json.dumps(metadata)})
    print('Status code: {}'.format(r.status_code))

    # Delete files if upload was a success.
    if r.status_code == 200:
        shutil.rmtree(dataFolder)

    # Remove from active uploads folder.
    del uploadingList[uploadingList.index(dataFolder)]
    
def rand_str(length = 8):
    return ''.join(random.sample(string.lowercase + string.digits, length))     

def datetimestamp(t = None):
    if t == None:
        return(time.strftime(format('%Y-%m-%d %H:%M:%S%z')))
    else:
        return(time.strftime(format('%Y-%m-%d %H:%M:%S%z'), t))

def timestamp():
    return(time.strftime(format('%H:%M:%S')))


