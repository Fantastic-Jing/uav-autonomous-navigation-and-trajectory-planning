# --- retro_cflib.py ---
import socket
import json
import time
import math

REACHED_THRESHOLD = 1.0   # meters: how close counts as "arrived"
REACHED_TIMEOUT   = 20.0  # seconds: give up after this


class MotionCommanderMock:
    def __init__(self, host='127.0.0.1', port=5000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, port))
            self.sock.settimeout(2.0)
            print("[cflib Mock] Connected to RetroFlight SITL.")
        except ConnectionRefusedError:
            print("[ERROR] Could not connect. Is RetroFlight running?")
            exit(1)

    def _send(self, payload):
        msg = json.dumps(payload) + "\n"
        self.sock.sendall(msg.encode('utf-8'))

    def _recv(self):
        """Read one newline-terminated JSON response."""
        buf = ""
        while "\n" not in buf:
            chunk = self.sock.recv(1024).decode('utf-8')
            if not chunk:
                raise ConnectionError("Connection closed by simulation.")
            buf += chunk
        line, _ = buf.split("\n", 1)
        return json.loads(line)

    def get_state(self):
        """
        Request the current UAV state from the simulation.

        Returns a dict with keys (all in meters / m/s / m/s²):
            time, x, y, z, vx, vy, vz, ax, ay, az, score
        """
        self._send({"cmd": "get_state"})
        return self._recv()

    def go_to(self, x, y, z, tolerance=REACHED_THRESHOLD, timeout=REACHED_TIMEOUT):
        """
        Send a waypoint and block until the UAV arrives or timeout expires.

        Args:
            x, y, z  : target position in meters
            tolerance: arrival radius in meters (default 0.2 m)
            timeout  : max wait time in seconds (default 10 s)
                       if 0, non-blocking (just send the command and return immediately)
        """
        self._send({"cmd": "go_to", "x": float(x), "y": float(y), "z": float(z)})
        print(f"[cflib Mock] go_to ({x}, {y}, {z}) — waiting for arrival...")

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                state = self.get_state()
            except Exception as e:
                print(f"[cflib Mock] get_state failed: {e}")
                break

            dx = state["x"] - x
            dy = state["y"] - y
            dz = state["z"] - z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            # print(f"[cflib Mock] Current position: ({state['x']:.2f}, {state['y']:.2f}, {state['z']:.2f}), distance to target: {dist:.2f} m")

            if dist < tolerance:
                print(f"[cflib Mock] Arrived at ({x}, {y}, {z}).")
                return

            time.sleep(0.05)

        if timeout > 0:
            print(f"[cflib Mock] Timeout reaching ({x}, {y}, {z}).")

    def get_batteries(self):
        """Returns list of battery positions in meters: [{"x": ..., "y": ...}, ...]"""
        self._send({"cmd": "get_batteries"})
        return self._recv()["batteries"]

    def get_map(self):
        """Returns the tilemap: width, height, and list of solid tile coordinates."""
        self._send({"cmd": "get_map"})
        return self._recv()

class CrazyflieMock:
    def __init__(self):
        # In the real API: call cf.open_link()
        # Here: initialize the mock-up commander
        self.commander = MotionCommanderMock()
