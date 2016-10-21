import os
import events
import random
import string
import json
import time
import requests

def make_dirs(dirs):
    """Makes the dirs in the list given"""
    try:
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
    except OSError as e:
        print(e)
        return False
    return True

def save_data(data, f = None):
    """Saves the data and recording in the toUpload folder."""
    # Make folder where the data and file will be saved.
    folder = os.path.join("toUpload", rand_str())
    if not make_dirs([folder]):
        print("Error with making folder when saving data: "+folder)
        return False

    # Move recording file, if there is one, into the folder made above.
    if f != None:
        _, ext = os.path.splitext(f)
        os.rename(f, os.path.join(folder, "file"+ext))

    # Save data as a json file.
    with open(os.path.join(folder, "metadata.json"), "w") as jsonFile:
        json.dump(data, jsonFile)

    # Make new event
    events.new_event(events.DATA_TO_UPLOAD, {"folder": folder})

def rand_str(length = 8):
    return ''.join(random.sample(string.lowercase + string.digits, length))     

def datetimestamp(t = None):
    if t == None:
        return(time.strftime(format('%Y-%m-%d %H:%M:%S%z')))
    else:
        return(time.strftime(format('%Y-%m-%d %H:%M:%S%z'), t))

def timestamp():
    return(time.strftime(format('%H:%M:%S')))

def inTimeRange(start, end):
    now = time.strftime(format('%H:%M'))
    start = int(start.split(":")[0])+int(start.split(":")[1])/100.0 #Change '10:23' into 10.23
    end = int(end.split(":")[0])+int(end.split(":")[1])/100.0
    now = int(now.split(":")[0])+int(now.split(":")[1])/100.0

    if (start < end): # range doesn't pass through midnight.
        return (start < now and now < end)
    else: # Rnage passes throgh midnight.
        return (start < now or now < end)

def ping(config):
    result = False
    url = config.get('server', 'url')
    print("Pinging server")
    try:
        r = requests.get(url+'/ping')
        if r.text == 'pong...':
            print('Pong...')
            result = True
    except:
        print("Error with connecting to server.")
        result = False
    return result
