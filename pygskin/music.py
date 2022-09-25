import pygame


class Music:
    REPEAT_FOREVER = -1

    def __init__(self, filename: str, volume: float = 1.0) -> None:
        self.filename = filename
        self.volume = volume

    def play(self, repeat_count: int = REPEAT_FOREVER) -> None:
        pygame.mixer.music.load(self.filename)
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.play(loops=repeat_count)
