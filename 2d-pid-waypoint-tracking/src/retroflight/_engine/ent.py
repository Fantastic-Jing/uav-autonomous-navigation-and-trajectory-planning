import numpy as np
from retroflight.config import TILE_SIZE, RADIUS_COLLISION
from retroflight._engine.tilemap import TileID

class Ent:
    def __init__(self, x, y, sim):
        self.type = "generic"
        self.sim = sim             # reference to the world/simulation this entity belongs to

        # State vector and physics:
        self.state = np.zeros(9, dtype=np.float32) # [x, y, z, vx, vy, vz, ax, ay, az]
        self.state[0] = x
        self.state[1] = y
        self.mass = 1.0            # mass of the entity, used for physics calculations
        self.thrust = np.zeros(3, dtype=np.float32) # thrust vector in x, y, z direction
        self.drag_coeff = 0.001    # default drag coefficient (c_D/mass)
        self.friction = 0.95       # friction coefficient, used to reduce velocity on collision

        # Game logic: use the think queue to schedule tasks, e.g.
        # in 0.5 seconds call think_func_foobar with some_context:
        #       ent.think_in(0.5, think_func_foobar, some_context)
        self.think_tasks = []      # List of (time_to_trigger, callback, context) tuples

        # Collision detection
        self.no_collision = False  # if True, this entity does not collide with tiles
        self.dead = False          # Remove this ent a the end of this frame if True

        # Visual properties:
        self.visible = True        # if False, this entity is not rendered
        self.draw_shadow = 0       # -1 = no shadow, 0 = small shadow, 1 = medium shadow, 2 = large shadow
        self.set_tile("null")      # set default tileset to "null", so it is not rendered
        self.pos_z_overlay = 0     # additional z position for rendering (e.g. oscillating, bouncing, etc.)
                                   # this is ignored by the physics engine, but used for rendering
        self.frame = 0             # current frame for animation
        self.animation = 0         # index of the current animation
        self.framerate_sec = 1.0 / 5.0 # switch frame every 1/x seconds
        self.framechange_sec = 0.0 # time accumulator for frame change

    def set_tile(self,name):
        """Set the tileset for this entity."""
        self.tileset = name
        self.tileid = -1 # reset tileid to -1, so it will be recached in the next step

    def on_collision(self, tilemap, collision_pos):
        # this method is called when a collision with a tile occurs
        # can be overridden by subclasses to implement custom behavior
        # e.g. to change the tile type on collision
        tx = int((self.x + 0.5 * TILE_SIZE) / TILE_SIZE)
        ty = int((self.y + 0.5 * TILE_SIZE) / TILE_SIZE)

    def on_ent_collision(self, other_ent):
        # this method is called when a collision with another entity occurs
        # can be overridden by subclasses to implement custom behavior
        pass

    def step(self, dt, time, tilemap):
        # update animation frame:
        self.framechange_sec += dt
        if self.framechange_sec >= self.framerate_sec:
            self.framechange_sec -= self.framerate_sec
            self.frame += 1
            if (self.frame > 255):
                self.frame = 0

        # Physics step:
        # calculate a desired new position based on velocity and test if it
        # collides with a tile
        # Note: No gravity for now. Will be added later.
        a = (1 / self.mass) * self.thrust # acceleration from thrust
        relative_wind = self.vel - self.sim.wind # relative wind speed
        self.acc = ( a - self.drag_coeff * relative_wind *
                     np.linalg.norm(relative_wind) / self.mass )
        self.vel += self.acc * dt # update velocity
        dp = self.vel * dt
        x0 = self.pos[0] + 0.5*TILE_SIZE # add offset x/y
        y0 = self.pos[1] + 0.5*TILE_SIZE
        vx = dp[0]
        vy = dp[1]
        s = 1.0 / TILE_SIZE
        box_half_size = RADIUS_COLLISION
        # collision test:
        new_x, new_y, new_vx, new_vy, hit, slide, collision_pos = \
            tilemap.move_box_tilespace_sweep(x0*s, y0*s, vx*s, vy*s, box_half_size)
        # on hit, only move until the collision point
        if hit:
            self.pos[0] = new_x*TILE_SIZE - 0.5*TILE_SIZE # subtract offset x/y
            self.pos[1] = new_y*TILE_SIZE - 0.5*TILE_SIZE
            self.vel[0] = self.friction * new_vx*TILE_SIZE / dt
            self.vel[1] = self.friction * new_vy*TILE_SIZE / dt
            self.on_collision(tilemap, collision_pos)
        else:
            self.pos += dp

        # Game logic: process think queue
        self._process_think_queue(time)

    def think_in(self, delay, callback, context=None):
        """Plan a function to be called in `delay` seconds."""
        trigger_time = self.sim.get_time() + delay
        self.think_tasks.append((trigger_time, callback, context))
        # warn if there are too many think tasks scheduled
        if len(self.think_tasks) > 100:
            print(f"Warning: {len(self.think_tasks)} think tasks scheduled for\
                    entity {self.type} at time {self.sim.get_time()}")

    def _process_think_queue(self, current_time):
        ready = [t for t in self.think_tasks if t[0] <= current_time]
        self.think_tasks = [t for t in self.think_tasks if t[0] > current_time]
        for _, cb, context in ready:
            cb(self, current_time, context)

    @property
    def pos(self):
        return self.state[0:3]
    @pos.setter
    def pos(self, value):
        self.state[0:3] = value
    @property
    def vel(self):
        return self.state[3:6]
    @vel.setter
    def vel(self, value):
        self.state[3:6] = value
    @property
    def acc(self):
        return self.state[6:9]
    @acc.setter
    def acc(self, value):
        self.state[6:9] = value
    @property
    def x(self):
        return self.state[0]
    @property
    def y(self):
        return self.state[1]
    @property
    def z(self):
        return self.state[2]
    @z.setter
    def z(self, value):
        self.state[2] = value
    @property
    def vx(self):
        return self.state[3]
    @vx.setter
    def vx(self, value):
        self.state[3] = value
    @property
    def vy(self):
        return self.state[4]
    @vy.setter
    def vy(self, value):
        self.state[4] = value
    @property
    def vz(self):
        return self.state[5]
    @vz.setter
    def vz(self, value):
        self.state[5] = value
    @property
    def ax(self):
        return self.state[6]
    @ax.setter
    def ax(self, value):
        self.state[6] = value
    @property
    def ay(self):
        return self.state[7]
    @ay.setter
    def ay(self, value):
        self.state[7] = value
    @property
    def az(self):
        return self.state[8]
    @az.setter
    def az(self, value):
        self.state[8] = value

# --- Think functions ---------------------------------------------------------
# Usage:
# For example, to schedule an entity to die after 0.5 seconds:
#   ent.think_in(0.5, think_func_die, None) # schedule to die after 0.5 seconds

def think_func_die(ent, time, context):
    """A simple think function to remove an entity after a delay."""
    ent.dead = True
    ent.no_collision = True

def think_func_toggle_visibility(ent, time, context):
    """A think function to toggle the visibility of an entity at 1/context seconds."""
    # Assert to make sure context is a reasonable time frame in seconds
    assert 0.0 < context <= 3600.0, "Context must be a float between 0.0 and 3600.0"
    ent.visible = not ent.visible
    ent.think_in(context, think_func_toggle_visibility, context)  # toggle visibility again after X seconds

