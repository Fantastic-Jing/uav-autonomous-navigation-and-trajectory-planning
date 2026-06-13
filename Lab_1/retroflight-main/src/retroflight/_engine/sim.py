import random
import numpy as np
import pygame
from retroflight.config import TILE_SIZE, WIDTH, HEIGHT, CFG_RANDOM_SEED
from retroflight._engine.tilemap import TileMap
from retroflight._engine.entitymanager import EntityManager 
from retroflight._engine.entplayer import EntPlayer
from retroflight._engine.entbattery import EntBattery

class UAVSim:
    def __init__(self, sound_manager):
        if CFG_RANDOM_SEED is not None:
            random.seed(CFG_RANDOM_SEED)
            np.random.seed(CFG_RANDOM_SEED)

        self.tilemap = TileMap()
        self.entities = EntityManager()
        self.sound_manager = sound_manager
        self.time = 0.0
        # add random steady state wind:
        self.wind = np.random.uniform(-5.5, 5.5, size=3).astype(np.float32) * TILE_SIZE  # random wind in x, y, z direction
        self.wind[2] = 0.0  # no vertical wind

        # adding a player
        new_player_pos_x = 1 * TILE_SIZE
        new_player_pos_y = 1 * TILE_SIZE
        newplayer = EntPlayer(new_player_pos_x, new_player_pos_y, self)
        self.playerid = self.entities.add(newplayer)

        # random battery spawn
        tiles_per_row = WIDTH // TILE_SIZE
        tiles_per_col = HEIGHT // TILE_SIZE
        area_total = self.tilemap.width * self.tilemap.height
        area_screen = tiles_per_row * tiles_per_col
        count = max(1, int(0.7 * area_total / area_screen))
        self.random_battery_spawn(count)

        # Score:
        self.score = 0

        self.mouse_pressed_prev = pygame.mouse.get_pressed()

    def random_battery_spawn(self, count=1):
        """Spawn a number of batteries at random positions."""
        while count > 0:
            x = np.random.randint(0, self.tilemap.width)
            y = np.random.randint(0, self.tilemap.height)
            if self.tilemap.is_solid(x, y):
                # If the tile is solid, we cannot place a battery here
                continue
            battery = EntBattery(x*TILE_SIZE, y*TILE_SIZE, sim=self)
            self.entities.add(battery)
            count -= 1

    def handle_input(self, cam_x, cam_y):
        thrust_x = 0
        thrust_y = 0
        thrust_z = 0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            thrust_y = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            thrust_y = +1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            thrust_x = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            thrust_x = +1
        if keys[pygame.K_q] or keys[pygame.K_PAGEUP]:
            thrust_z = +1
        if keys[pygame.K_e] or keys[pygame.K_PAGEDOWN]:
            thrust_z = -1

        if self.playerid >= 0:
            ent = self.entities.get(self.playerid)
            ent.key_input(thrust_x, thrust_y, thrust_z)

            mouse_pressed = pygame.mouse.get_pressed()
            if mouse_pressed[0] and not self.mouse_pressed_prev[0]:
                self.entities.spawn_particles(
                    ent.pos[0], ent.pos[1]-ent.pos[2], vx=ent.vel[0], vy=ent.vel[1],
                    pos_spread=0.5, lifetime=1.0, count=4
                    )
            self.mouse_pressed_prev = mouse_pressed


    def step(self, dt, time):
        self.time = time
        self.entities.step(dt, time, self.tilemap)

    def get_time(self):
        """Get the current simulation time."""
        return self.time
