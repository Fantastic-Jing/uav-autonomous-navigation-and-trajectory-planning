from retroflight.config import TILE_SIZE
from retroflight._engine.ent import Ent
import math

class EntBattery(Ent):
    def __init__(self, x, y, sim):
        super().__init__(x, y, sim)

        self.type = "battery"
        self.set_tile("battery")
        self.draw_shadow = 0 # small shadow
        self.drag_coeff = 0 # don't want the battery to be affected by wind

    def step(self, dt, time, tilemap):
        super().step(dt, time, tilemap)

        self.pos_z_overlay = math.sin(2 * math.pi * 0.5 * time) * TILE_SIZE / 10.0
