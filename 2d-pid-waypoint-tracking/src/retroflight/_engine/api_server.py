# --- retroflight/api_server.py ---
import socket
import json
import threading
import numpy as np
from typing import Any, Dict, Optional
from retroflight.config import TILE_SIZE # tile size in pixels

class APIServer(threading.Thread):
    """
    A TCP server running in a background thread to receive external
    control commands for the UAV simulation.

    Implemented commands:
        - "go_to": Move the UAV to a specified (x, y, z) coordinate in meters.
            Example: {"cmd": "go_to", "x": 10, "y": 5, "z": 3}

    Attributes:
        sim (Any): The main simulation instance to be controlled.
        host (str): The IP address the server binds to.
        port (int): The TCP/IP network port the server listens on.
    """
    def __init__(self, sim, host='127.0.0.1', port=5000):
        super().__init__()
        self.sim = sim
        self.host = host
        self.port = port
        self.daemon = True # Stop thread, on main program exit
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        print(f"[API Server] Listening on {self.host}:{self.port}...")

    def run(self):
        """
        The API server main loop. Accepts incoming TCP/IP connections and
        buffers streaming data for JSON processing.
        """
        while True:
            conn, addr = self.sock.accept()
            print(f"[API Server] Connected by {addr}")
            try:
                buffer = ""
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    buffer += data.decode('utf-8')

                    # Process JSON commands line by line
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        response = self.handle_command(json.loads(line))
                        if response is not None:
                            conn.sendall((json.dumps(response) + '\n').encode('utf-8'))
            except Exception as e:
                print(f"[API Server] Connection error: {e}")
            finally:
                conn.close()
                print("[API Server] Disconnected.")
                ent = self.sim.entities.get(self.sim.playerid)
                if ent is not None:
                    ent.external_api_active = False
                    print("[API Server] External API deactivated for player entity.")

    def handle_command(self, payload: Dict[str, Any]):
        """
        Processes incoming JSON commands and updates simulation state.

        Args:
            payload: A dictionary containing the command and parameters.
                Expected format for 'go_to':
                {"cmd": "go_to", "x": float, "y": float, "z": float}
        """

        if payload.get("cmd") == "go_to":
            # --- METER TO PIXEL CONVERSION ---
            # 1 meter is 1 TILE_SIZE
            target_x = payload["x"] * TILE_SIZE
            target_y = payload["y"] * TILE_SIZE
            target_z = payload["z"] * TILE_SIZE

            ent = self.sim.entities.get(self.sim.playerid)
            if ent is not None:
                if ent.external_api_active is False:
                    print("[API Server] External API activated for player entity.")
                ent.external_api_active = True
                ent.target_setpoint = np.array([target_x, target_y, target_z], dtype=np.float32)
                print("New waypoint received: ", ent.target_setpoint)
            return None

        if payload.get("cmd") == "get_state":
            ent = self.sim.entities.get(self.sim.playerid)
            if ent is None:
                return {"error": "no player"}
            s = ent.state / TILE_SIZE  # convert to Metern
            return {
                "time": self.sim.time,
                "x":  float(s[0]), "y":  float(s[1]), "z":  float(s[2]),
                "vx": float(s[3]), "vy": float(s[4]), "vz": float(s[5]),
                "ax": float(s[6]), "ay": float(s[7]), "az": float(s[8]),
                "score": self.sim.score,
            }

        if payload.get("cmd") == "get_batteries":
            batteries = []
            for ent in self.sim.entities.entities:
                if ent.type == "battery" and not ent.no_collision:
                    batteries.append({
                        "x": float(ent.pos[0] / TILE_SIZE),
                        "y": float(ent.pos[1] / TILE_SIZE),
                    })
            return {"batteries": batteries}

        if payload.get("cmd") == "get_map":
            tilemap = self.sim.tilemap
            grid = []
            for y in range(tilemap.height):
                row = ""
                for x in range(tilemap.width):
                    row += "#" if tilemap.is_solid(x, y) else "."
                grid.append(row)
            return {"width": tilemap.width, "height": tilemap.height, "grid": grid}

