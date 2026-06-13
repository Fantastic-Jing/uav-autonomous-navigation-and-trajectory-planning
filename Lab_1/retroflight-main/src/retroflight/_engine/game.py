import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" # Hide pygame startup message
import pygame
from retroflight.config import WIDTH, HEIGHT, FPS, TILE_SIZE, CAMSPEED
from retroflight._engine.sim import UAVSim
from retroflight._engine.renderer import Renderer
from retroflight._engine.assetmanager import AssetManager
from retroflight._engine.soundmanager import SoundManager

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("RetroFlight")
        self.clock = pygame.time.Clock()

        self.asset_manager = AssetManager()
        self.asset_manager.register("null",      "WAD/null.png", animation=False)
        self.asset_manager.register("tiles",     "WAD/tileset.png", animation=False)
        self.asset_manager.register("uav",       "WAD/uav2.png")
        self.asset_manager.register("battery",   "WAD/battery.png")
        self.asset_manager.register("shadow",    "WAD/shadow.png")
        self.asset_manager.register("part_gold", "WAD/particles.png")

        self.asset_manager.duplicate_sheet_colored("battery", "battery_white", (255, 255, 255))

        self.sound_manager = SoundManager()
        self.sound_manager.register("battery",    "WAD/battery.mp3")

        self.sim = UAVSim(self.sound_manager)
        self.renderer = Renderer(self.screen, self.asset_manager)

    def run(self):
        running = True
        dt_fixed = 1.0 / FPS
        accumulator = 0.0
        time = 0.0

        while running:
            frame_dt = self.clock.tick(FPS) / 1000.0 # sleep if we are running too fast
            accumulator += min(frame_dt, 0.05)

            cx = int(self.renderer.cam_x)
            cy = int(self.renderer.cam_y)
            self.sim.handle_input(cx, cy)

            while accumulator >= dt_fixed:
                time += dt_fixed
                self.sim.step(dt_fixed, time)
                accumulator -= dt_fixed

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                if event.type == pygame.QUIT:
                    running = False

            # drag camera along player position
            ent = self.sim.entities.get(self.sim.playerid)
            if ent is not None:
                self.renderer.cam_x = -ent.pos[0] - 0.5*TILE_SIZE + WIDTH/2
                self.renderer.cam_y = -ent.pos[1] - 0.5*TILE_SIZE + HEIGHT/2
                self.renderer.cam_x = max(-(self.sim.tilemap.width*TILE_SIZE - self.renderer.screen.get_width()), self.renderer.cam_x)
                self.renderer.cam_y = max(-(self.sim.tilemap.height*TILE_SIZE - self.renderer.screen.get_height()), self.renderer.cam_y)
                self.renderer.cam_x = min(0, self.renderer.cam_x)
                self.renderer.cam_y = min(0, self.renderer.cam_y)
                self.renderer.cam_x = int(self.renderer.cam_x)
                self.renderer.cam_y = int(self.renderer.cam_y)
            else:
                # Camera movement
                keys = pygame.key.get_pressed()
                if keys[pygame.K_UP]:
                    self.renderer.cam_y += CAMSPEED*frame_dt
                    self.renderer.cam_y = min(0, self.renderer.cam_y)
                    self.renderer.cam_y = max(-(self.sim.tilemap.height*TILE_SIZE - self.renderer.screen.get_height()), self.renderer.cam_y)
                if keys[pygame.K_DOWN]:
                    self.renderer.cam_y -= CAMSPEED*frame_dt
                    self.renderer.cam_y = min(0, self.renderer.cam_y)
                    self.renderer.cam_y = max(-(self.sim.tilemap.height*TILE_SIZE - self.renderer.screen.get_height()), self.renderer.cam_y)
                if keys[pygame.K_LEFT]:
                    self.renderer.cam_x += CAMSPEED*frame_dt
                    self.renderer.cam_x = min(0, self.renderer.cam_x)
                    self.renderer.cam_x = max(-(self.sim.tilemap.width*TILE_SIZE - self.renderer.screen.get_width()), self.renderer.cam_x)
                if keys[pygame.K_RIGHT]:
                    self.renderer.cam_x -= CAMSPEED*frame_dt
                    self.renderer.cam_x = min(0, self.renderer.cam_x)
                    self.renderer.cam_x = max(-(self.sim.tilemap.width*TILE_SIZE - self.renderer.screen.get_width()), self.renderer.cam_x)

            self.renderer.draw(self.sim)

            # Draw debug pathfinding
            mouse_pressed = pygame.mouse.get_pressed()
            if mouse_pressed[2]:  # right button held
                ent = self.sim.entities.get(self.sim.playerid)
                mx, my = pygame.mouse.get_pos()
                x0 = ent.pos[0] + 0.5*TILE_SIZE
                y0 = ent.pos[1] + 0.5*TILE_SIZE - ent.pos[2]
                vx = mx - x0 - cx
                vy = my - y0 - cy

                start_px = int(x0)
                start_py = int(y0)
                end_px   = int(start_px + vx)
                end_py   = int(start_py + vy)

                # Draw desired full path (in blue)
                pygame.draw.line(self.renderer.screen, (0, 0, 255), (start_px+cx, start_py+cy), (end_px+cx, end_py+cy), 2)

                # Draw start point marker (white)
                pygame.draw.circle(self.renderer.screen, (255, 255, 255), (start_px+cx, start_py+cy), 4)

                # Convert to tile units for DDA
                result = self.sim.tilemap.dda_ray_cast_segment(x0/TILE_SIZE, y0/TILE_SIZE, vx/TILE_SIZE, vy/TILE_SIZE)
                if result is not None:
                    t_hit, tile_x, tile_y, normal_x, normal_y = result
                    hit_x = x0 + vx * t_hit
                    hit_y = y0 + vy * t_hit

                    hit_px = int(hit_x)
                    hit_py = int(hit_y)
                    pygame.draw.circle(self.renderer.screen, (255, 0, 0), (hit_px+cx, hit_py+cy), 5)
                    pygame.draw.line(self.renderer.screen, (0,255,0), (hit_px+cx, hit_py+cy), (hit_px + normal_x*0.5*TILE_SIZE + cx, hit_py + normal_y*0.5*TILE_SIZE + cy), 1)
                    pygame.draw.circle(self.renderer.screen, (0, 255, 0), (hit_px + normal_x*0.5*TILE_SIZE + cx, hit_py + normal_y*0.5*TILE_SIZE + cy), 1)
                    # bx = -vx*t_hit
                    # by = -vy*t_hit
                    # radius = (TILE_SIZE/2.0)
                    # s = radius/(bx*normal_x + by*normal_y)
                    # backx = hit_x + bx*s
                    # backy = hit_y + by*s
                    # pygame.draw.circle(self.renderer.screen, (0, 0, 255), (int(backx+cx), int(backy+cy)), radius)

            pygame.display.flip()

        pygame.quit()

