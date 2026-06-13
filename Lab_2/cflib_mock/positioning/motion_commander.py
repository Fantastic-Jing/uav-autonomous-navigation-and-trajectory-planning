import time

class MotionCommander:
    last_session = None

    def __init__(self, scf, default_height=0.5):
        self.scf = scf
        self.default_height = float(default_height)
        self._commands = []

    def __enter__(self):
        # Simulate takeoff issued on enter
        self._commands.append({"cmd": "takeoff", "height": self.default_height})
        MotionCommander.last_session = self
        return self

    def __exit__(self, exc_type, exc, tb):
        # Simulate landing on exit
        self._commands.append({"cmd": "land"})

    # Movement primitives
    def forward(self, distance: float, velocity: float = 0.5):
        self._commands.append({"cmd": "forward", "distance": float(distance), "velocity": float(velocity)})

    def back(self, distance: float, velocity: float = 0.5):
        self._commands.append({"cmd": "back", "distance": float(distance), "velocity": float(velocity)})

    def left(self, distance: float, velocity: float = 0.5):
        self._commands.append({"cmd": "left", "distance": float(distance), "velocity": float(velocity)})

    def right(self, distance: float, velocity: float = 0.5):
        self._commands.append({"cmd": "right", "distance": float(distance), "velocity": float(velocity)})

    def stop(self):
        self._commands.append({"cmd": "stop"})

    # Helpers used by the test harness
    def has_cmd(self, cmd: str) -> bool:
        return any(c.get("cmd") == cmd for c in self._commands)

    def movement_commands(self):
        # Return lateral movement commands (with distances)
        return [c for c in self._commands if c.get("cmd") in ("forward", "back", "left", "right")]

    def all_commands(self):
        return list(self._commands)

