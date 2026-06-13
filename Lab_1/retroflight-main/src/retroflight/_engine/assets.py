import pygame
from retroflight.config import TILE_SIZE, TILE_SIZE_SOURCE

class TilesheetAnimation:
    def __init__(self, frames_2d, frame_w, frame_h, tile_size):
        self.animations = frames_2d        # 2D list: animations[y][x]
        self.frame_w = frame_w             # number of frames per animation
        self.frame_h = frame_h             # number of animations (rows)
        self.tile_size = tile_size

    def get_frame(self, anim_index, frame_index):
        return self.animations[anim_index % self.frame_h][frame_index % self.frame_w]

    def duplicate_colored(self, color):
        """Create a duplicate of the tilesheet with a color overlay."""
        new_frames_2d = []
        for row in self.animations:
            new_row = []
            for frame in row:
                colored_frame = frame.copy()
                colored_frame.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)  # delete color, keep Alpha
                colored_frame.fill(color + (0,), special_flags=pygame.BLEND_RGBA_ADD)
                new_row.append(colored_frame)
            new_frames_2d.append(new_row)
        return TilesheetAnimation(new_frames_2d, self.frame_w, self.frame_h, self.tile_size)

def load_anim_tilesheet(path, source_tile_size=TILE_SIZE_SOURCE, target_tile_size=TILE_SIZE):
    """Load a tilesheet animation from a file.
    Note: every line in the tilesheet is considered a separate animation.
    Use this to load an animated tilesheet where each row represents a different animation.
    Args:
        path (str): Path to the tilesheet image file.
        source_tile_size (int): Size of the tiles in the source image.
        target_tile_size (int): Size of the tiles in the target image.
    Returns:
        TilesheetAnimation: An object containing the frames of the animation.
    """
    image = pygame.image.load(path).convert_alpha()
    w, h = image.get_width(), image.get_height()
    frame_w = w // source_tile_size
    frame_h = h // source_tile_size

    if target_tile_size is None:
        target_tile_size = source_tile_size

    scale = target_tile_size / source_tile_size
    frames_2d = []

    for row in range(frame_h):
        row_frames = []
        for col in range(frame_w):
            rect = pygame.Rect(col * source_tile_size, row * source_tile_size,
                               source_tile_size, source_tile_size)
            frame = image.subsurface(rect)
            if scale != 1.0:
                frame = pygame.transform.scale(frame, (target_tile_size, target_tile_size))
            row_frames.append(frame)
        frames_2d.append(row_frames)

    return TilesheetAnimation(frames_2d, frame_w, frame_h, target_tile_size)

def load_tilesheet(path, source_tile_size=TILE_SIZE_SOURCE, target_tile_size=TILE_SIZE):
    """Load a tilesheet from a file.
    Note: Use this to load a set of tiles that are not animated. E.g. background tiles.
    Args:
        path (str): Path to the tilesheet image file.
        source_tile_size (int): Size of the tiles in the source image.
        target_tile_size (int): Size of the tiles in the target image.
    Returns:
        TilesheetAnimation: An object containing a single "animation", which is a single row of frames.
    """
    image = pygame.image.load(path).convert_alpha()
    w, h = image.get_width(), image.get_height()
    frame_w = w // source_tile_size
    frame_h = h // source_tile_size

    if target_tile_size is None:
        target_tile_size = source_tile_size

    scale = target_tile_size / source_tile_size
    frames_2d = []
    row_frames = []

    for row in range(frame_h):
        for col in range(frame_w):
            rect = pygame.Rect(col * source_tile_size, row * source_tile_size,
                               source_tile_size, source_tile_size)
            frame = image.subsurface(rect)
            if scale != 1.0:
                frame = pygame.transform.scale(frame, (target_tile_size, target_tile_size))
            row_frames.append(frame)

    frames_2d.append(row_frames) # store all frames in a single row

    return TilesheetAnimation(frames_2d, frame_w*frame_h, 1, target_tile_size)

