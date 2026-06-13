# Minimal mock of cflib for unit testing
_scenario = {
    "vbat": 4.0,
    "varPX": 0.001,
    "roll": 0.0,
    "pitch": 0.0,
    "vx": 0.0,
    "vy": 0.0,
    "rssi": 40,
    "lh_deck": True,
}

def set_scenario(overrides: dict):
    _scenario.update(overrides)

def reset_scenario():
    global _scenario
    _scenario = {
        "vbat": 4.0,
        "varPX": 0.001,
        "roll": 0.0,
        "pitch": 0.0,
        "vx": 0.0,
        "vy": 0.0,
        "rssi": 40,
        "lh_deck": True,
    }

def get_value(name: str):
    return _scenario.get(name)

