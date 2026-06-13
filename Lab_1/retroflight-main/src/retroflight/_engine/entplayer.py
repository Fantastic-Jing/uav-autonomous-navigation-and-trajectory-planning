from retroflight.config import TILE_SIZE, CFG_RESPAWN_BATTERIES
from retroflight._engine.tilemap import TileID
from retroflight._engine.ent import Ent, think_func_die, think_func_toggle_visibility
from retroflight.controller import UAVController
import math
import numpy as np

def dir_to_animation_index(x, y):
    # Depending on the movement direction we want to set an animation,
    # this converts the x, y direction to an animation id.
    # x is -1, 0, or 1 (left, none, right)
    # y is -1, 0, or 1 (down, none, up)

    # The lookup table is as follows:
    #  1 2 3
    #  8 0 4
    #  7 6 5
    # e.g. if x = 1 and y = 0, we want to return 4 (moving right),
    # and the UAV tileset must have at animation with id 4 a
    # moving right animation.

    x = int(round(x)) # make sure x and y are integers
    y = int(round(y))
    assert(x >= -1 and x <= 1
           and y >= -1 and y <= 1), "x and y must be in range [-1, 1]"
    lookup = [1, 2, 3, 8, 0, 4, 7, 6, 5]
    index = (y + 1)*3  + (x+1)
    return lookup[index]

class EntPlayer(Ent):
    def __init__(self, x, y, sim):
        super().__init__(x, y, sim)
        self.z = TILE_SIZE/4
        self.type = "player"
        self.set_tile("uav")
        self.draw_shadow = 1  # medium shadow
        self.max_thrust = 18.0 * TILE_SIZE

        self.controller = UAVController()
        self.target_setpoint = np.array(self.pos, dtype=np.float32)
        self.external_api_active = False

    def step(self, dt, time, tilemap):
        super().step(dt, time, tilemap)

        if self.external_api_active:
            # convert from pixel to meters:
            self.thrust = self.controller.compute_thrust(self.state/TILE_SIZE, self.target_setpoint/TILE_SIZE, dt, time)*TILE_SIZE
            # make sure thrust is float32:
            self.thrust = self.thrust.astype(np.float32)
            # clip to max thrust:
            self.thrust = np.clip(self.thrust, -self.max_thrust, self.max_thrust)

        # purely visual oscillation of the UAV:
        self.pos_z_overlay = math.sin(2 * math.pi * 2.0 * time) * TILE_SIZE / 32.0

        s = 1.0 / TILE_SIZE
        # limit max. altitude of UAV
        if self.pos[2] > 2 * TILE_SIZE:
            self.pos[2] = 2 * TILE_SIZE
        if self.pos[2] < 0:
            self.pos[2] = 0.0
            tx = int((self.x + 0.5 * TILE_SIZE) * s)
            ty = int((self.y + 0.5 * TILE_SIZE) * s)
            # if we are on the ground, mow the grass (just for fun):
            if tilemap.get_tile(tx, ty) == TileID.GRASS:
                tilemap.set_tile(tx, ty, TileID.MOWED_GRASS)

    def on_collision(self, tilemap, collision_pos):
        super().on_collision(tilemap, collision_pos) # call base method to handle basic collision response
        self.controller.on_collision(self.state/TILE_SIZE, "level")

    def on_ent_collision(self, other_ent):

        self.controller.on_collision(self.state/TILE_SIZE, other_ent.type)

        if other_ent.type == "battery" and self.z < TILE_SIZE*0.5: # pick up battery if close to the ground
            # visual feedback for picking up a battery (spawn particles):
            self.sim.entities.spawn_particles(
                self.pos[0], self.pos[1]-self.pos[2], vx=self.vel[0]*0.25, vy=self.vel[1]*0.25,
                pos_spread=0.5, lifetime=1.0, count=4
                )
            other_ent.no_collision = True # disable collision with this item
            other_ent.set_tile("battery_white") # visual feedback for picked up battery
            other_ent.think_in(0.5, think_func_die) # schedule to die after 0.5 seconds
            other_ent.think_in(0.0, think_func_toggle_visibility, 0.05) # blink for 20hz until it dies
            other_ent.vx = self.vx * 0.2 # add some momentum to the picked up battery
            other_ent.vy = self.vy * 0.2
            if CFG_RESPAWN_BATTERIES:
                self.sim.random_battery_spawn(count=1) # create a new battery at a random position
            self.sim.score += 10

            # play pick-up sound:
            sound_idx = self.sim.sound_manager.get_sound_index("battery")
            self.sim.sound_manager.play_sound(sound_idx)

    def key_input(self, thrust_x, thrust_y, thrust_z):
        if self.external_api_active:
            # print("[EntPlayer] Ignoring manual input because external API is active.")
            return # ignore manual input if external API is active

        self.animation = dir_to_animation_index(thrust_x, thrust_y)

        self.thrust = np.array([thrust_x, thrust_y, 0.0], dtype=np.float32) * self.max_thrust
        # no altitude control for now, directly set vertical velocity, but we can add it later:
        self.vz = thrust_z*2*TILE_SIZE

