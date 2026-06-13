class SoundObject:
    def __init__(self, name, path):
        self.name = name
        self.load(path)

    def load(self, path):
        import pygame
        self.sound = pygame.mixer.Sound(path)
        self.path = path

    def play(self, left_volume=1.0, right_volume=1.0):
        if self.sound:
            channel = self.sound.play()
            channel.set_volume(left_volume, right_volume)
            return channel
        return None

    def stop(self):
        if self.sound:
            self.sound.stop()

class SoundManager:
    def __init__(self):
        self.sound_names = []     # index --> name
        self.sound_lookup = {}    # name  --> index
        self.sound_list = []      # index --> SoundObject

    def register(self, name, path):
        # check if the sound is already registered
        if name in self.sound_lookup:
            return
        index = len(self.sound_list)
        self.sound_names.append(name)
        self.sound_lookup[name] = index
        self.sound_list.append(SoundObject(name, path))

    def get_sound_index(self, name: str) -> int:
        return self.sound_lookup[name]

    def get_sound(self, index: int):
        return self.sheets_list[index]

    def play_sound_by_name(self, name: str):
        if name in self.sound_lookup:
            index = self.sound_lookup[name]
            self.sound_list[index].play()
        else:
            raise ValueError(f"Sound '{name}' not registered.")

    def play_sound(self, index: int):
        if 0 <= index < len(self.sound_list):
            self.sound_list[index].play()
        else:
            raise IndexError(f"Sound index {index} out of range.")

