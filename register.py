import requests
from detectionSystem import setup, detect

reader = setup()
url = 'http://192.168.1.101:5000/'

while True:

    c = input('--')
    
    if c == exit:
        break
    
    if not c or c =='scan':
        data = detect(reader)
    
        if data['success']:
            epcs = data['uuids']
    
            vMan = requests.get(url + '/verifyManifest/?man=' + json.dumps(epcs))
    
            epc_list = [x for x in epcs if x not in vMan]
    
            print(epc_list)
    
            while True:
    
                d = input('index: ')
    
                if d == 'back':
                    break
    
                try:
                    tag = epc_list[int(d)]
    
                except ValueError:
                    pass
    
                else:
                    name = input('name: ')
                    age = input('age:  ')
                    gender = input('gender: ')
    
                    if name and age and epc and age and gender:
                        requests.get('http://192.168.1.101:5000/newPassenger/?name={}&tag={}&age={}&gender={}'.format(name, tag, age, gender))
    
                        break
