import mercury


def setup():
    while True:
        try:
            reader = mercury.Reader('tmr:///dev/ttyS0')
            reader.set_read_plan([1], 'GEN2')
            reader.set_region('NA2')
    
            return reader
        
        except TypeError:
            print('broke')

    
def detect(r):  # returns the manifest
    # r should be a mercury reader object
    while True:
        try:
            epcs = list(map(lambda t: t.epc.decode(), r.read()))
        
            return {'success': True, 'uuids': epcs}
        
        except TypeError:
            print('timeout during read')


if __name__ == '__main__':
    print(detect())
