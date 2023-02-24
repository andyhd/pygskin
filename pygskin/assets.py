import filetype
import pygame


class Asset:
    class NotRecognised(Exception):
        pass

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def load(self) -> None:
        raise NotImplementedError

    @classmethod
    def prep(cls, filename: str) -> None:
        kind = filetype.guess(filename)
        if kind is None:
            raise Asset.NotRecognised(filename)

        if kind.mime.startswith("image/"):
            return Image(filename)

        if kind.mime.startswith("audio/"):
            if kind.mime.startwith("audio/mp3"):
                return Music(filename)
            return Sound(filename)

        if kind.mime.startswith("application/font-"):
            return Font(filename)


class Image(Asset):
    def __init__(self, filename: str) -> None:
        super().__init__(filename)
        self.image: pygame.Surface | None = None

    def load(self) -> None:
        if not self.image:
            self.image = pygame.image.load(self.filename)


class Sound(Asset):
    def __init__(self, filename: str, volume: float = 1.0) -> None:
        super().__init__(filename)
        self.sound: pygame.mixer.Sound | None = None
        self.volume = volume

    def load(self) -> None:
        if pygame.mixer and not pygame.mixer.get_init():
            pygame.mixer.init()
        if not self.sound and pygame.mixer and pygame.mixer.get_init():
            self.sound = pygame.mixer.Sound(self.filename)
            self.sound.set_volume(self.volume)

    def play(self, *args, **kwargs) -> None:
        if not self.sound:
            self.load()

        if self.sound:
            self.sound.play()


class Music(Asset):
    REPEAT_FOREVER = -1

    def __init__(self, filename: str, volume: float = 1.0) -> None:
        super().__init__(filename)
        self.volume = volume

    def load(self) -> None:
        pygame.mixer.music.load(self.filename)
        pygame.mixer.music.set_volume(self.volume)

    def play(self, repeat_count: int = REPEAT_FOREVER) -> None:
        pygame.mixer.music.play(loops=repeat_count)
