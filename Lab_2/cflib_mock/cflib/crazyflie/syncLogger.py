import time
from .. import get_value

class SyncLogger:
    def __init__(self, scf, logconf):
        self.scf = scf
        self.logconf = logconf
        self._running = False

    def __enter__(self):
        self._running = True
        return self

    def __exit__(self, exc_type, exc, tb):
        self._running = False

    def __iter__(self):
        # Return an iterator that yields (timestamp, data_dict)
        return self

    def __next__(self):
        if not self._running:
            raise StopIteration
        data = {}
        for name, fmt in self.logconf.variables:
            if name == 'pm.vbat':
                data[name] = get_value('vbat')
            elif name == 'kalman.varPX':
                data[name] = get_value('varPX')
            elif name == 'stateEstimate.roll':
                data[name] = get_value('roll')
            elif name == 'stateEstimate.pitch':
                data[name] = get_value('pitch')
            elif name == 'stateEstimate.vx':
                data[name] = get_value('vx')
            elif name == 'stateEstimate.vy':
                data[name] = get_value('vy')
            elif name == 'radio.rssi':
                data[name] = get_value('rssi')
            else:
                data[name] = None
        time.sleep(0.05)
        return (time.time(), data)

