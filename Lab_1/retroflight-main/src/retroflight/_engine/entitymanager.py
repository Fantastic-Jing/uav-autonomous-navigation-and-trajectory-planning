import numpy as np
from retroflight.config import TILE_SIZE, RADIUS_COLLISION
from retroflight._engine.quadtreenode import QuadtreeNode

def fake_normal_dist(T, s):
    return T + s * (np.random.rand() + np.random.rand() - 1)

def random_2d_velocity(T_speed, s_speed):
    angle = 2 * np.pi * np.random.rand()
    speed = max(T_speed*0.1, fake_normal_dist(T_speed, s_speed))
    vx = np.cos(angle) * speed
    vy = np.sin(angle) * speed
    vz = 0.0
    return np.array([vx, vy, vz])

class Particle:
    def __init__(self, x, y, vx, vy, pos_spread=0.5, lifetime=1.0):
        self.pos_x = x + np.random.uniform(-pos_spread, pos_spread)
        self.pos_y = y + np.random.uniform(-pos_spread, pos_spread)
        self.pos_z = 0 + np.random.uniform(-pos_spread, pos_spread)
        v = random_2d_velocity(200.0, 50.0)
        vx_rand, vy_rand, vz_rand = v
        self.vx = vx + vx_rand
        self.vy = vy + vy_rand
        self.vz = vz_rand * 0.0
        self.age = 0.0
        self.lifetime = max(0.1, fake_normal_dist(lifetime, 0.5))
        self.dead = False
        self.animation = 0  # index of the current animation frame


class EntityManager:
    def __init__(self):
        self.entities = []
        self.particles = []
        self.particle_frame = 0
        self.particle_framerate_sec = 1.0 / 10.0  # switch frame every 1/10 seconds
        self.particle_framechange_sec = 0.0 # time accumulator for particle frame change
        self.particle_drag_coeff = 2.0  # drag coefficient for particles

    def add(self, ent):
        index = len(self.entities)
        self.entities.append(ent)
        return index

    def get(self, index):
        if 0 <= index < len(self.entities):
            return self.entities[index]
        return None

    def spawn_particles(self, x, y, vx=0.0, vy=0.0, pos_spread=0.5, lifetime=1.0, count=10):
        for _ in range(count):
            particle = Particle(x, y, vx, vy, pos_spread, lifetime)
            particle.animation = np.random.randint(0, 4)
            self.particles.append(particle)

    def step(self, dt, time, tilemap):
        for ent in self.entities:
            ent.step(dt, time, tilemap)

        # Create a quadtree for collision detection
        quadtree = QuadtreeNode(0, 0, tilemap.width * TILE_SIZE, tilemap.height * TILE_SIZE)
        for ent in self.entities:
            quadtree.insert(ent)
        # Perform collision detection between entities
        for ent in self.entities:
            if ent.no_collision:
                continue
            radius_px = RADIUS_COLLISION * TILE_SIZE
            nearby = quadtree.query(ent.x - radius_px, ent.y - radius_px, 2*radius_px, 2*radius_px)
            for other in nearby:
                if other is ent or other.no_collision:
                    continue
                if self.check_collision(ent, other):
                    ent.on_ent_collision(other)

        self.particle_framechange_sec += dt
        if self.particle_framechange_sec >= self.particle_framerate_sec:
            self.particle_framechange_sec -= self.particle_framerate_sec
            self.particle_frame += 1
            if self.particle_frame > 255:
                self.particle_frame = 0

        for p in self.particles:
            if not p.dead:
                p.age += dt
                if p.age >= p.lifetime:
                    p.dead = True
                else:
                    p.vx -= self.particle_drag_coeff * dt * p.vx
                    p.vy -= self.particle_drag_coeff * dt * p.vy
                    p.vz -= self.particle_drag_coeff * dt * p.vz
                    p.pos_x += p.vx * dt
                    p.pos_y += p.vy * dt
                    p.pos_z += p.vz * dt

        self.particles = [p for p in self.particles if not p.dead]
        self.entities = [ent for ent in self.entities if not ent.dead]

    def check_collision(self, ent_a, ent_b, radius=0.5):
        dx = ent_a.x - ent_b.x
        dy = ent_a.y - ent_b.y
        dist_sq = dx * dx + dy * dy
        max_dist = 2 * radius * RADIUS_COLLISION * TILE_SIZE
        return dist_sq < (max_dist * max_dist)
