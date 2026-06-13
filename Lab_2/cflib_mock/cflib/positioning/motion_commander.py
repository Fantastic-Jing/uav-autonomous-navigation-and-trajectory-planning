"""
Mock MotionCommander - records all movement commands for later analysis.

The test runner inspects `MotionCommander.last_session` after the test
code runs to verify the trajectory.
"""

import time


class MotionCommander:
    """
    Drop-in mock for cflib.positioning.motion_commander.MotionCommander.

    Records every command issued so the test harness can verify:
      - takeoff height
      - all four rectangle sides present
      - landing called
      - velocities are within sane bounds
    """

    # Filled by the most recent context-manager session
    last_session: "MotionCommander | None" = None

    def __init__(self, scf, default_height: float = 0.5):
        self._scf = scf
        self.default_height = default_height
        self.commands: list[dict] = []   # ordered list of issued commands
        self._flying = False

    # ------------------------------------------------------------------
    # Context manager — auto take-off / land
    # ------------------------------------------------------------------
    def __enter__(self):
        MotionCommander.last_session = self
        self._record("takeoff", height=self.default_height)
        self._flying = True
        print(f"[MOCK] MotionCommander: take-off to {self.default_height} m")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._flying:
            self._record("land")
            self._flying = False
            print("[MOCK] MotionCommander: auto-land (context exit)")
        return False

    # ------------------------------------------------------------------
    # Movement commands
    # ------------------------------------------------------------------
    def _record(self, cmd: str, **kwargs):
        entry = {"cmd": cmd, **kwargs}
        self.commands.append(entry)

    def forward(self, distance: float, velocity: float = 0.2):
        print(f"[MOCK] forward  {distance:.2f} m  @ {velocity:.2f} m/s")
        self._record("forward", distance=distance, velocity=velocity)
        time.sleep(0.01)

    def back(self, distance: float, velocity: float = 0.2):
        print(f"[MOCK] back     {distance:.2f} m  @ {velocity:.2f} m/s")
        self._record("back", distance=distance, velocity=velocity)
        time.sleep(0.01)

    def left(self, distance: float, velocity: float = 0.2):
        print(f"[MOCK] left     {distance:.2f} m  @ {velocity:.2f} m/s")
        self._record("left", distance=distance, velocity=velocity)
        time.sleep(0.01)

    def right(self, distance: float, velocity: float = 0.2):
        print(f"[MOCK] right    {distance:.2f} m  @ {velocity:.2f} m/s")
        self._record("right", distance=distance, velocity=velocity)
        time.sleep(0.01)

    def up(self, distance: float, velocity: float = 0.2):
        print(f"[MOCK] up       {distance:.2f} m  @ {velocity:.2f} m/s")
        self._record("up", distance=distance, velocity=velocity)
        time.sleep(0.01)

    def down(self, distance: float, velocity: float = 0.2):
        print(f"[MOCK] down     {distance:.2f} m  @ {velocity:.2f} m/s")
        self._record("down", distance=distance, velocity=velocity)
        time.sleep(0.01)

    def turn_left(self, angle: float, rate: float = 20.0):
        print(f"[MOCK] turn_left  {angle:.1f}°  @ {rate:.1f} °/s")
        self._record("turn_left", angle=angle, rate=rate)
        time.sleep(0.01)

    def turn_right(self, angle: float, rate: float = 20.0):
        print(f"[MOCK] turn_right {angle:.1f}°  @ {rate:.1f} °/s")
        self._record("turn_right", angle=angle, rate=rate)
        time.sleep(0.01)

    def land(self, velocity: float = 0.1):
        print(f"[MOCK] land  @ {velocity:.2f} m/s")
        self._record("land", velocity=velocity)
        self._flying = False

    def stop(self):
        print("[MOCK] stop")
        self._record("stop")

    def start_down(self, velocity: float = 0.1):
        print(f"[MOCK] start_down @ {velocity:.2f} m/s")
        self._record("start_down", velocity=velocity)

    def start_forward(self, velocity: float = 0.2):
        self._record("start_forward", velocity=velocity)

    def start_back(self, velocity: float = 0.2):
        self._record("start_back", velocity=velocity)

    def start_left(self, velocity: float = 0.2):
        self._record("start_left", velocity=velocity)

    def start_right(self, velocity: float = 0.2):
        self._record("start_right", velocity=velocity)

    # ------------------------------------------------------------------
    # Helpers the test harness uses
    # ------------------------------------------------------------------
    def movement_commands(self) -> list[dict]:
        """Return only the directional move commands (no takeoff/land)."""
        skip = {"takeoff", "land", "stop", "start_down",
                "start_forward", "start_back", "start_left", "start_right"}
        return [c for c in self.commands if c["cmd"] not in skip]

    def has_cmd(self, cmd: str) -> bool:
        return any(c["cmd"] == cmd for c in self.commands)
