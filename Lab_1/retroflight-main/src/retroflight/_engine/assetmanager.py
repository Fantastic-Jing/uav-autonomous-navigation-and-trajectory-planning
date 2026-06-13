from retroflight.config import TILE_SIZE, TILE_SIZE_SOURCE
from retroflight._engine.assets import load_tilesheet, load_anim_tilesheet

class AssetManager:
    """
    The AssetManager is responsible for loading and managing all game assets, including tilesheets and animations.
    """

    def __init__(self):
        self.sheet_names = []      # index --> name
        self.sheet_lookup = {}     # name  --> index
        self.sheets_list = []      # index --> TilesheetAnimation

    def register(self, name, path, animation=True):
        """
        This can be used to load both static tilesheets (animation=False) and
        animated tilesheets (animation=True). Animations are a single image
        where each row is a separate animation sequence. For example, a UAV
        sheet might have 4 rows: idle, move, takeoff, land.

        Example:

            register("battery", "WAD/battery.png")

            Use the ent.set_tile("battery") so that entity will use the
            "battery" tilesheet.

        Args:
            name (str): A unique name to identify the tilesheet/animation later.
            path (str): The file path to the tilesheet image (pngs).
            animation (bool): Whether to load the tilesheet as an animation
                              (True) or a static sheet (False). If True, each row in the
                              tilesheet is treated as a separate animation.
        """
        index = len(self.sheets_list)
        print("Loading: {}".format(path))
        if animation:
            sheet = load_anim_tilesheet(path, TILE_SIZE_SOURCE, TILE_SIZE)
        else:
            sheet = load_tilesheet(path, TILE_SIZE_SOURCE, TILE_SIZE)
        self.sheet_names.append(name)
        self.sheet_lookup[name] = index
        self.sheets_list.append(sheet)

    def get_sheet_index(self, name: str) -> int:
        if name not in self.sheet_lookup:
            return self.sheet_lookup["null"]
        else:
            return self.sheet_lookup[name]

    def get_sheet(self, index: int):
        """
        Get the TilesheetAnimation object for the given index.
        This can be used to retrieve the frames for rendering entities or tiles.
        Example:

            sheet_index = asset_manager.get_sheet_index("uav")
            uav_sheet = asset_manager.get_sheet(sheet_index)

        """
        return self.sheets_list[index]

    def duplicate_sheet_colored(self, name, new_name, color: tuple):
        """
        Create a duplicate of the sheet at the given index with a color overlay.

        Purpose: This is useful for creating variations of a base tilesheet
        (e.g., different colored drones) without needing separate image files
        for each variation.
        """
        index = self.get_sheet_index(name)
        sheet = self.sheets_list[index]
        new_sheet = sheet.duplicate_colored(color)
        self.sheets_list.append(new_sheet)
        new_index = len(self.sheets_list) - 1
        self.sheet_names.append(new_name)
        self.sheet_lookup[new_name] = new_index

        return new_index

