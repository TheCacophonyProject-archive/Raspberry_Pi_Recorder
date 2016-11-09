import os
import shutil
import ConfigParser
import util
import requests
import json

configPath = ""
privateConfigPath = ""

def init(cp, pcp):
    """Checks that device is registered and has JWT.
    returns false if init failed."""
    
    global configPath
    configPath = cp
    global privateConfigPath
    privateConfigPath = pcp

    jwt = get_private_setting('jwt')

    if (jwt == None or jwt == ""):
        return update_jwt()
    else:
        return True         

def register(devicename = None):
    """Register device using given device name,
    if none is givne then creates a random one.
    password is saved to private config file."""

    if devicename == None or devicename == "":
        devicename = util.rand_str(12)
    group = get_setting('device', 'group')
    if group == None or group == "":
        print("No group is set. Set group in device section in config file.")
        return False    
    password = util.rand_str(20)

    serverUrl = get_setting('server', 'url')
    url = serverUrl + '/api/v1/devices'
    try:
        payload = {'password': password,
                   'devicename': devicename,
                   'group': group}
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            j = json.loads(r.text)
            set_private_setting('password', password)
            set_private_setting('jwt', j['token'])
            set_setting('device', 'devicename', devicename)
            return True
        elif r.status_code == 400:
            j = json.loads(r.text)
            print('Error with register')
            print(j['messages'])
            return False
        else:
            print("Error with register.")
            return False
    except Exception as e:
        print("Error with register")
        print(e)
        return False

def update_jwt():
    """Gets a new JWT from the server"""
    password = get_private_setting('password')
    devicename = get_setting('device', 'devicename')

    if devicename == None or devicename == "":
        print("Can't get JWT as no devicename is saved. Will register again.")
        return register(util.rand_str(12))

    if password == None or password == "":
        print("Can't get JWT as no password is saved. Will register again.")
        return register(util.rand_str(12))

    serverUrl = get_setting('server', 'url')
    url = serverUrl + '/authenticate_device'
    try:
        payload = {'password': get_private_setting('password'),
                   'devicename': get_setting('device', 'devicename')
                   }
        print("Getting new JWT")
        r = requests.post(url, data = payload)
        if r.status_code == 200:
            j = json.loads(r.text)
            print("New jwt from server.")
            set_private_setting('jwt', j['token'])
            return True
        elif r.status_code == 401:
            print("401 when authenticating, will re-register.")
            return register(util.rand_str(12))
        else:
            print("Error with device authenticating device request.")
            return False
    except:
        print("Error with connecting to server")
        return False
    
def update_settigns(settings):
    """Takes a JSON and saves it to a config file."""
    print("Save settings... TODO")

def set_private_setting(key, value):
    # Make private config file if there is not one.
    if not os.path.isfile(privateConfigPath):
        f = file(privateConfigPath, "w")
        f.close()
    config = ConfigParser.RawConfigParser()
    config.read(privateConfigPath)

    if not config.has_section('private'):
        config.add_section('private')

    config.set('private', key, value)
    
    with open(privateConfigPath, 'w') as configFile:
        config.write(configFile)
                           
def get_private_setting(key):
    config = ConfigParser.RawConfigParser()
    config.read(privateConfigPath)
    if (config.has_option('private', key)):
        return config.get('private', key)
    else:
        return None
    
def set_setting(section, key, value):
    if not os.path.isfile(configPath):
        print("Can't find config file")
        return None

    config = ConfigParser.RawConfigParser()
    config.read(configPath)

    if not config.has_section(section):
        config.add_section(section)

    config.set(section, key, value)

    with open(configPath, 'w') as configFile:
        config.write(configFile)

def get_setting(section, key):
    config = ConfigParser.RawConfigParser()
    config.read(configPath)
    if (config.has_option(section, key)):
        return config.get(section, key)
    else:
        return None
