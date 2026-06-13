from .. import get_value

class ParamMock:
    def add_update_callback(self, group, name, cb):
        # Immediately invoke callback with current lighthouse deck state
        lh = get_value('lh_deck')
        value_str = '1' if lh else '0'
        try:
            cb(None, value_str)
        except TypeError:
            # Some callbacks may expect different signature
            cb(value_str)

class SupervisorMock:
    def send_arming_request(self, val):
        self.armed = bool(val)

class Crazyflie:
    def __init__(self):
        self.param = ParamMock()
        self.supervisor = SupervisorMock()

