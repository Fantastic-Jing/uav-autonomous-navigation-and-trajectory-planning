import pygame
from retroflight.config import TILE_SIZE, TILE_SIZE_SOURCE
from retroflight._engine.assets import load_tilesheet
from retroflight._engine.assetmanager import AssetManager

class Renderer:
    def __init__(self, screen, asset_manager):
        self.screen = screen
        self.bg_color = (180, 220, 255)
        self.asset_manager = asset_manager

        self.tiles      = asset_manager.get_sheet(asset_manager.get_sheet_index("tiles"))
        self.tileshadow = asset_manager.get_sheet(asset_manager.get_sheet_index("shadow"))

        self.cam_x = 0
        self.cam_y = 0

        self.font = pygame.font.Font('WAD/pixel.ttf', 8)  # None uses the default font

    def draw(self, sim):
        # self.screen.fill(self.bg_color)

        # Draw tilemap
        for y in range(sim.tilemap.height):
            for x in range(sim.tilemap.width):
                tile_id = sim.tilemap.get_tile(x, y)
                tile = self.tiles.get_frame(0, tile_id)
                self.screen.blit(
                    tile,
                    (x * TILE_SIZE + int(self.cam_x), y * TILE_SIZE + int(self.cam_y))
                )

        # Painter's algorithm: draw entities from back to front
        # Sort by y-position: ent.pos[1]
        sorted_ents = sorted(
                sim.entities.entities, key=lambda ent: ent.pos[1])
        for ent in sorted_ents:
            self.draw_ent_shadow(ent)
        for ent in sorted_ents:
            self.draw_ent(ent)

        self.draw_particles(sim)

        textstr = "Score: " + str(sim.score) + " | Wind: x/y " + str(int(sim.wind[0])) + "/" + str(int(sim.wind[1]))
        text = self.font.render(textstr, False, (255, 255, 255))
        text_shadow = self.font.render(textstr, False, (0, 0, 0))
        # scale up the text to match the tile size
        text = pygame.transform.scale(text, (int(text.get_width() * TILE_SIZE / TILE_SIZE_SOURCE),
                                              int(text.get_height() * TILE_SIZE / TILE_SIZE_SOURCE)))
        text_shadow = pygame.transform.scale(text_shadow, (int(text_shadow.get_width() * TILE_SIZE / TILE_SIZE_SOURCE),
                                              int(text_shadow.get_height() * TILE_SIZE / TILE_SIZE_SOURCE)))
        self.screen.blit(text_shadow, (15, 15))
        self.screen.blit(text, (10, 10))

    def draw_ent_shadow(self, ent):
        if ent.draw_shadow >= 0:
            cx = self.cam_x
            cy = self.cam_y
            self.screen.blit(self.tileshadow.get_frame(ent.draw_shadow,0),
                             (int(ent.pos[0]+cx), int(ent.pos[1]+cy)))

    def draw_ent(self, ent):
        if ent.visible is False:
            return

        cx = self.cam_x
        cy = self.cam_y

        if ent.draw_shadow >= 0:
            self.screen.blit(self.tileshadow.get_frame(ent.draw_shadow,0),
                             (int(ent.pos[0]+cx), int(ent.pos[1]+cy)))

        if ent.tileid == -1:
            ent.tileid = self.asset_manager.get_sheet_index(ent.tileset)
        tilesheet = self.asset_manager.get_sheet(ent.tileid)
        tile = tilesheet.get_frame(ent.animation, ent.frame)
        self.screen.blit(tile, (int(ent.pos[0])+cx, int(ent.pos[1]-ent.pos[2]+cy+ent.pos_z_overlay)))

    def draw_particles(self, sim):
        particle_sheet_id = self.asset_manager.get_sheet_index("part_gold")
        particle_sheet = self.asset_manager.get_sheet(particle_sheet_id)
        particles = sim.entities.particles
        frame_index = sim.entities.particle_frame

        for p in particles:
            tile = particle_sheet.get_frame(p.animation, frame_index)
            self.screen.blit(tile, (int(p.pos_x + self.cam_x), int(p.pos_y + self.cam_y)))

