"""
cflib_mock — shared scenario state.

The test runner sets `SCENARIO` before importing the test script.
All mock sub-modules read from here.
"""

# ---------------------------------------------------------------------------
# Default (healthy) telemetry values
# ---------------------------------------------------------------------------
SCENARIO: dict = {
    "vbat":           3.9,   # V  - healthy: > 3.7
    "roll":           0.3,   # °  - healthy: |x| < 2.0
    "pitch":          0.2,   # °
    "pos_x":          0.1,   # m
    "pos_y":         -0.05,  # m
    "vx":             0.01,  # m/s - healthy: |x| < 0.2
    "vy":             0.02,  # m/s
    "varPX":          0.003, # m²  - healthy: sqrt < 0.08
    "varPY":          0.003, # m²
    "rssi":           45,    # dBm - healthy: > 80
    "lh_deck":        True,  # Lighthouse deck attached?
}

def set_scenario(overrides: dict):
    """Merge overrides into SCENARIO. Call from test runner."""
    SCENARIO.update(overrides)

def reset_scenario():
    """Reset to healthy defaults."""
    SCENARIO.clear()
    SCENARIO.update({
        "vbat":   3.9,
        "roll":   0.3,
        "pitch":  0.2,
        "pos_x":  0.1,
        "pos_y": -0.05,
        "vx":     0.01,
        "vy":     0.02,
        "varPX":  0.003,
        "varPY":  0.003,
        "rssi":   45,
        "lh_deck": True,
    })
