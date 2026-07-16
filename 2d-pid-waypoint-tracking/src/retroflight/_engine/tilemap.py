import random
import numpy as np

class TileID:
    UNDEFINED = -1
    GRASS = 0
    WALL = 1
    SPECIAL_WALL = 2
    LAB_FLOOR = 3
    LAB_VENT = 4
    BIGTREE = 5
    BUSH = 6
    SMALLTREE = 7
    MOWED_GRASS = 8

class TileMap:
    def __init__(self, width=40, height=30):
        self.width = width
        self.height = height
        self.map = np.zeros((height, width), dtype=np.uint8)
        self.mapsolid = np.zeros((height, width), dtype=np.uint8)

        self.generate_random_level()

    def generate_random_level(self):
            self.map[:, :] = TileID.GRASS
            self.mapsolid[:, :] = 0
            door_sides = ["top", "bottom", "left", "right"]

            room_count = 8
            for _ in range(room_count):
                rw = random.randint(4, 10)
                rh = random.randint(4, 8)
                rx = random.randint(5, self.width - rw - 1)
                ry = random.randint(5, self.height - rh - 1)

                self.map[ry+1:ry+rh-1, rx+1:rx+rw-1] = TileID.LAB_FLOOR
                self.mapsolid[ry+1:ry+rh-1, rx+1:rx+rw-1] = 0

                # Walls
                self.map[ry:ry+rh, rx] = TileID.WALL
                self.map[ry:ry+rh, rx+rw-1] = TileID.WALL
                self.map[ry, rx:rx+rw] = TileID.WALL
                self.map[ry+rh-1, rx:rx+rw] = TileID.WALL
                self.mapsolid[self.map == 1] = 1

                side = random.choice(door_sides)
                if side == "top":
                    dx = random.randint(1, rw - 2)
                    self.map[ry, rx + dx] = TileID.LAB_FLOOR
                    self.mapsolid[ry, rx + dx] = 0
                elif side == "bottom":
                    dx = random.randint(1, rw - 2)
                    self.map[ry + rh - 1, rx + dx] = TileID.LAB_FLOOR
                    self.mapsolid[ry + rh - 1, rx + dx] = 0
                elif side == "left":
                    dy = random.randint(1, rh - 2)
                    self.map[ry + dy, rx] = TileID.LAB_FLOOR
                    self.mapsolid[ry + dy, rx] = 0
                elif side == "right":
                    dy = random.randint(1, rh - 2)
                    self.map[ry + dy, rx + rw - 1] = TileID.LAB_FLOOR
                    self.mapsolid[ry + dy, rx + rw - 1] = 0

            for _ in range(40):
                tx = random.randint(0, self.width - 1)
                ty = random.randint(0, self.height - 1)
                if self.map[ty, tx] == 0:
                    self.map[ty, tx] = random.choice(list({TileID.BIGTREE,TileID.BUSH,TileID.SMALLTREE}))
                    self.mapsolid[ty, tx] = 1

            for _ in range(40):
                tx = random.randint(0, self.width - 1)
                ty = random.randint(0, self.height - 1)
                if self.map[ty, tx] == 3:
                    self.map[ty, tx] = TileID.LAB_VENT
                    self.mapsolid[ty, tx] = 1

            self.map[:, 0] = TileID.WALL
            self.mapsolid[:, 0] = 1
            self.map[:, self.width - 1] = TileID.WALL
            self.mapsolid[:, self.width - 1] = 1
            self.map[0, :] = TileID.WALL
            self.mapsolid[0, :] = 1
            self.map[self.height - 1, :] = TileID.WALL
            self.mapsolid[self.height - 1, :] = 1

            self.mapsolid[1, 1] = 0 # clear top-left corner

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.map[y, x]
        else:
            return TileID.UNDEFINED

    def set_tile(self, x, y, tile_id):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.map[y, x] = tile_id

    def is_solid(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.mapsolid[y, x] > 0
        else:
            return True

    def dda_ray_cast_segment(self, x0, y0, vx, vy, max_steps=1000):
        """
        Casts a ray from (x0, y0) in tile coordinates along vector (vx, vy),
        and returns the first solid tile hit within the segment.

        Parameters:
            x0, y0 (float): Starting position in tile units.
            vx, vy (float): Ray vector in tile units.
            max_steps (int): Safety cap on number of tile steps.

        Returns:
            (t, tile_x, tile_y, normal) if hit occurs:
                t:      fractional distance along (vx, vy) in [0, 1]
                tile_x, tile_y: coordinates of solid tile hit
                normal: (nx, ny), surface normal of impacted face (normalized)

            None if no hit occurs.
        """
        from math import floor

        dx, dy = vx, vy
        ray_len = (dx ** 2 + dy ** 2) ** 0.5
        if ray_len == 0:
            return None

        # Normalize direction
        dx /= ray_len
        dy /= ray_len

        tile_x = int(floor(x0))
        tile_y = int(floor(y0))

        step_x = 1 if dx > 0 else -1
        step_y = 1 if dy > 0 else -1

        # Distance to walk along ray to get to next tile in x direction
        delta_dist_x = abs(1 / dx) if dx != 0 else float('inf')
        # Distance to walk along ray to get to next tile in y direction
        delta_dist_y = abs(1 / dy) if dy != 0 else float('inf')

        # Distance along ray to next tile border in x direction
        if dx > 0:
            side_dist_x = (tile_x + 1 - x0) * delta_dist_x
        elif dx < 0:
            side_dist_x = (x0 - tile_x) * delta_dist_x
        else:
            side_dist_x = float('inf')
        # Distance along ray to next tile border in y direction
        if dy > 0:
            side_dist_y = (tile_y + 1 - y0) * delta_dist_y
        elif dy < 0:
            side_dist_y = (y0 - tile_y) * delta_dist_y
        else:
            side_dist_y = float('inf')

        traveled_dist = 0.0
        max_dist = ray_len

        for _ in range(max_steps):
            if side_dist_x < side_dist_y:
                traveled_dist = side_dist_x
                tile_x += step_x
                side_dist_x += delta_dist_x
                hit_axis = 'x'
            else:
                traveled_dist = side_dist_y
                tile_y += step_y
                side_dist_y += delta_dist_y
                hit_axis = 'y'

            if traveled_dist > max_dist:
                break

            if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
                if self.is_solid(tile_x, tile_y):
                    t = traveled_dist / ray_len
                    if hit_axis == 'x':
                        normal_x = -step_x
                        normal_y = 0
                    else:
                        normal_x = 0
                        normal_y = -step_y
                    return t, tile_x, tile_y, normal_x, normal_y

        return None

    def move_box_tilespace_sweep(self, x, y, vx, vy, box_half_size=0.5, max_step=0.25):
        steps = int(max(abs(vx), abs(vy)) / max_step) + 1
        dx = vx / steps
        dy = vy / steps
        new_vx = vx
        new_vy = vy

        for _ in range(steps):
            x, y, new_vx, new_vy, hit, slide, hitpos = self._move_box_tilespace(x, y, dx, dy, box_half_size)
            if hit:
                break

        return x, y, new_vx, new_vy, hit, slide, hitpos

    def _move_box_tilespace(self, x, y, vx, vy, box_half_size=0.5):
        new_x = x
        new_y = y

        hit = False
        slide = False
        collision_pos = None

        # ---- X ----
        tx_min = int((x + vx - box_half_size))
        tx_max = int((x + vx + box_half_size - 1e-5))
        ty_min = int((y - box_half_size))
        ty_max = int((y + box_half_size - 1e-5))

        blocked_x = False
        for tx in range(tx_min, tx_max + 1):
            for ty in range(ty_min, ty_max + 1):
                if 0 <= tx < self.width and 0 <= ty < self.height:
                    if self.is_solid(tx, ty):
                        blocked_x = True
                        hit = True
                        break
            if blocked_x:
                break

        if not blocked_x:
            new_x += vx
        else:
            vx = 0
            slide = True
            collision_pos = (new_x, y)  # last valid point before Y movement

        # ---- Y ----
        tx_min = int((new_x - box_half_size))
        tx_max = int((new_x + box_half_size - 1e-5))
        ty_min = int((y + vy - box_half_size))
        ty_max = int((y + vy + box_half_size - 1e-5))

        blocked_y = False
        for tx in range(tx_min, tx_max + 1):
            for ty in range(ty_min, ty_max + 1):
                if 0 <= tx < self.width and 0 <= ty < self.height:
                    if self.is_solid(tx, ty):
                        blocked_y = True
                        hit = True
                        break
            if blocked_y:
                break

        if not blocked_y:
            new_y += vy
        else:
            vy = 0
            slide = True
            collision_pos = (new_x, new_y) if collision_pos is None else collision_pos

        # Final safety check
        tx_min = int((new_x - box_half_size))
        tx_max = int((new_x + box_half_size - 1e-5))
        ty_min = int((new_y - box_half_size))
        ty_max = int((new_y + box_half_size - 1e-5))

        for tx in range(tx_min, tx_max + 1):
            for ty in range(ty_min, ty_max + 1):
                if 0 <= tx < self.width and 0 <= ty < self.height:
                    if self.is_solid(tx, ty):
                        # Prevent movement — return last safe position
                        return x, y, vx, vy, True, False, (x, y)

        return new_x, new_y, vx, vy, hit, slide, collision_pos
