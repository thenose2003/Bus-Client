import mercury


def setup():
    reader = mercury.Reader('tmr:///dev/ttys0')
    reader.set_read_plan([1], 'GEN2')
    reader.set_region('NA2')

    return reader


def detect(r):  # returns the manifest
    # r should be a mercury reader object

    epcs = list(map(lambda t: t.epc.decode(), r.read()))

    return {'success': True, 'uuids': epcs}


if __name__ == '__main__':
    print(detect())
