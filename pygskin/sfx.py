import pygame


class SFX:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.sound: pygame.mixer.Sound | None = None

    def load(self) -> None:
        if not self.sound and pygame.mixer and pygame.mixer.get_init():
            self.sound = pygame.mixer.Sound(self.filename)

    def play(self) -> None:
        if not self.sound:
            self.load()

        if self.sound:
            self.sound.play()
