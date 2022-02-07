import json
import time
from detectionSystem import detect, setup
from gps import location
from bt import sendInfo, removeInfo
from datetime import datetime
import requests

if __name__ != '__main__':  # Raises an error if someone tries running this as a package for some reason
    raise "This isn't a package idiot"

url = 'http://192.168.1.101:5000/'
busID = open('ID.txt', 'r').read()
info = {}  # Defines the information json
sec = -5  # Defines seconds in the minute
going = True
manifest = []
# manifest is updated to contain an up to date manifest
reader = setup()

# TODO add a empty request to make sure you get data for all people on startup

while going:

    while abs(datetime.now().second - sec) < 3:
        time.sleep(1)
    sec = datetime.now().second

    # scan is an intermediate variable between the actual scanner and manifest
    # it will be compared with manifest to detect changes
    scan = detect(reader)

    if scan['success']:  # if the scanner returned anything

        if sorted(scan['uuids']) != sorted(manifest):  # detect a change in manifest

            manifest = scan['uuids']  # set the new manifest

            try:  # try to update the server
                print(manifest)
                info = requests.get(
                    url + 'requestInfo/?id=' + busID + '&manifest=' + json.dumps({'uuids': manifest}) +
                    '&long=' + str(location()[0]) + '&lat=' + str(location()[1])).json()

            except requests.exceptions.ConnectionError:  # print an error if that fails
                print('ERROR: Could not contact the server')

            else:
                if info['data']:  # if there is new data
                    p_new = info['data'].values()

                    sendInfo(p_new)

                if info['departs']:
                    departs = info['departs']

                    removeInfo(departs)

        else:
            requests.get(url + 'locationPing/?id={}&long={}&lat={}'.format(busID, location()[0], location()[1]))

    if datetime.now().minute % 5 == 0 and datetime.now().second < 10:
        with open('info.json', 'w') as json_file:
            json.dump(info, json_file, indent=4)
            json_file.close()
