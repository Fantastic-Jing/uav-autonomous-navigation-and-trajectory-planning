from .. import get_value

class ParamMock:
    def add_update_callback(self, group, name, cb):
        # Immediately invoke callback with current lighthouse deck state
        lh = get_value('lh_deck')
        value_str = '1' if lh else '0'
        try:
            cb(None, value_str)
        except TypeError:
            cb(value_str)

class SupervisorMock:
    def send_arming_request(self, val):
        self.armed = bool(val)

class Crazyflie:
    def __init__(self):
        self.param = ParamMock()
        self.supervisor = SupervisorMock()


class SyncCrazyflie:
    """Minimal SyncCrazyflie placeholder used by the test harness.

    Tests construct instances with SyncCrazyflie.__new__ and then set
    attributes directly (uri, cf). We provide the class here so it can be
    imported from cflib.crazyflie.
    """
    pass


