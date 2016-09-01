import threading
import events
import shutil
import os
import requests
import json

serverUrl = None

class MainThread(threading.Thread):
    """Thread manage uploading data."""
    def __init__(self, configParser):
        threading.Thread.__init__(self)
        self.events = []
        self._stop = False
        self.eventWait = threading.Event()
        self.name = "Upload manager"
        print("Created new '{name}' thread".format(name = self.name))

        global serverUrl
        self.uploadThreads = []
        serverUrl = configParser.get('server', 'url')
        
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
        elif self.event.type == events.DATA_TO_UPLOAD:
            self.new_upload()
            
    def stop(self):
        print("Stopping '{name}'.".format(name = self.name))
        # Some 'final' things go here.
        self._stop = True

    def new_upload(self):
        # Save data as a json file into the new folder
        newUploadThread = upload(self.event.extra["folder"])
        newUploadThread.start()
        self.uploadThreads.append(newUploadThread)

class upload(threading.Thread):
    """Uploads data to the server."""
    def __init__(self, dataFolder):
        threading.Thread.__init__(self)
        self.dataFolder = dataFolder

    def run(self):
        files = {}
        for f in os.listdir(self.dataFolder):
            name, ext = os.path.splitext(f)
            if name == 'metadata' and ext == '.json':
                metadataFile = open(os.path.join(self.dataFolder, f))
                metadata = json.loads(''.join(metadataFile.readlines()))
                dataType = metadata['__type__']
                del metadata['__type__']
            elif name == 'file':
                files['file'] = open(os.path.join(self.dataFolder, f))
            else:
                print("Error: unknown file in folder: " + f)

        if dataType == 'videoRecording':
            url = serverUrl + '/api/v1/videoRecordings'
        else:
            print("Datatype '{}' unknown.".format(dataType))
            return

        # Post and print status code.
        print('Posting data...')
        try:
            r = requests.post(url, files = files, data = {'data': json.dumps(metadata)})
            print('Status code: {}'.format(r.status_code))

            # Delete files if upload was a success.
            if r.status_code == 200:
                shutil.rmtree(self.dataFolder)
        except:
            print("Error: With uploadin to database.")
