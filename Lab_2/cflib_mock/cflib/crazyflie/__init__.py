"""
Mock cflib.crazyflie — Crazyflie, SyncCrazyflie, LogConfig, SyncLogger.

Behaviour:
- SyncCrazyflie works as a context manager and exposes .cf
- LogConfig tracks which variables were added (for byte-budget check)
- SyncLogger yields one fake log entry built from cflib.SCENARIO
- Param callbacks for 'deck' / 'bcLighthouse4' fire automatically
"""

import time
import cflib  # shared scenario state


# ---------------------------------------------------------------------------
# Byte sizes per cflib type string
# ---------------------------------------------------------------------------
_TYPE_SIZES = {
    "float":  4,
    "FP16":   2,
    "uint8":  1,
    "uint16": 2,
    "uint32": 4,
    "int8":   1,
    "int16":  2,
    "int32":  4,
}

_PAYLOAD_LIMIT = 26  # bytes per LogConfig packet


# ---------------------------------------------------------------------------
# LogConfig
# ---------------------------------------------------------------------------
class LogConfig:
    def __init__(self, name: str, period_in_ms: int = 100):
        self.name = name
        self.period_in_ms = period_in_ms
        self._variables = []   # (full_name, type_str)

    def add_variable(self, name: str, type_str: str = "float"):
        self._variables.append((name, type_str))

    def _payload_bytes(self):
        return sum(_TYPE_SIZES.get(t, 4) for _, t in self._variables)

    def _check_payload(self):
        used = self._payload_bytes()
        if used > _PAYLOAD_LIMIT:
            raise RuntimeError(
                f"[MOCK] LogConfig '{self.name}' exceeds 26-byte limit: "
                f"{used} bytes used by {len(self._variables)} variables. "
                f"Use FP16 (2 B) instead of float (4 B) where possible."
            )


# ---------------------------------------------------------------------------
# Helper: build a fake data dict from current SCENARIO
# ---------------------------------------------------------------------------
_VARIABLE_MAP = {
    "pm.vbat":              lambda s: s["vbat"],
    "stateEstimate.roll":   lambda s: s["roll"],
    "stateEstimate.pitch":  lambda s: s["pitch"],
    "stateEstimate.x":      lambda s: s["pos_x"],
    "stateEstimate.y":      lambda s: s["pos_y"],
    "stateEstimate.vx":     lambda s: s["vx"],
    "stateEstimate.vy":     lambda s: s["vy"],
    "kalman.varPX":         lambda s: s["varPX"],
    "kalman.varPY":         lambda s: s["varPY"],
    "radio.rssi":           lambda s: s["rssi"],
}

def _build_data(logconf):
    s = cflib.SCENARIO
    data = {}
    for name, _ in logconf._variables:
        if name in _VARIABLE_MAP:
            data[name] = _VARIABLE_MAP[name](s)
        else:
            data[name] = 0.0
    return data


# ---------------------------------------------------------------------------
# SyncLogger
# ---------------------------------------------------------------------------
class SyncLogger:
    def __init__(self, scf, logconf):
        self._scf = scf
        self._logconf = logconf

    def __enter__(self):
        self._logconf._check_payload()
        return self

    def __exit__(self, *_):
        pass

    def __iter__(self):
        while True:
            data = _build_data(self._logconf)
            yield (int(time.time() * 1000), data, self._logconf)
            time.sleep(0.05)


# ---------------------------------------------------------------------------
# Supervisor stub
# ---------------------------------------------------------------------------
class _Supervisor:
    def send_arming_request(self, arm: bool):
        state = "ARMED" if arm else "DISARMED"
        print(f"[MOCK] Supervisor: drone {state}")


# ---------------------------------------------------------------------------
# Param stub
# ---------------------------------------------------------------------------
class _Param:
    def __init__(self):
        self._callbacks = []

    def add_update_callback(self, group, name, cb):
        self._callbacks.append((group, name, cb))
        if group == "deck" and name == "bcLighthouse4":
            value = "1" if cflib.SCENARIO.get("lh_deck", True) else "0"
            cb(f"{group}.{name}", value)


# ---------------------------------------------------------------------------
# Crazyflie stub
# ---------------------------------------------------------------------------
class Crazyflie:
    def __init__(self, rw_cache="./cache"):
        self.supervisor = _Supervisor()
        self.param = _Param()


# ---------------------------------------------------------------------------
# SyncCrazyflie
# ---------------------------------------------------------------------------
class SyncCrazyflie:
    def __init__(self, uri, cf=None):
        self.uri = uri
        self.cf = cf or Crazyflie()

    def __enter__(self):
        print(f"[MOCK] Connected to {self.uri}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            print(f"[MOCK] Disconnected from {self.uri}")
        return False
