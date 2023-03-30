from functools import partial
from typing import Any
from typing import Callable
from typing import ClassVar

import filetype
import pygame

from pygskin.pubsub import message


class Asset:
    class NotRecognised(Exception):
        pass

    load: ClassVar[Callable[[str], Any]]

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self._loaded = False
        self.loaded = message()

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.data = self.load(self.filename)
            self._loaded = True
            self.loaded()

    @classmethod
    def prep(cls, filename: str) -> None:
        kind = filetype.guess(filename)
        if kind is None:
            raise Asset.NotRecognised(filename)

        if kind.mime.startswith("image/"):
            pygame.display.init()
            return Image(filename)

        if kind.mime.startswith("audio/"):
            if pygame.mixer and not pygame.mixer.get_init():
                pygame.mixer.init()
            if kind.mime.startwith("audio/mp3"):
                return Music(filename)
            return Sound(filename)

        if kind.mime.startswith("application/font-"):
            if not pygame.font.get_init():
                pygame.font.init()
            return Font(filename)


class Image(Asset):
    load = pygame.image.load


class Sound(Asset):
    load = pygame.mixer.Sound

    def __init__(self, filename: str, volume: float = 1.0) -> None:
        super().__init__(filename)
        self.loaded.subscribe(partial(self.data.set_volume, volume))

    def play(self, *args, **kwargs) -> None:
        self.ensure_loaded()
        self.data.play()


class Music(Asset):
    load = pygame.mixer.music.load

    REPEAT_FOREVER = -1

    def __init__(self, filename: str, volume: float = 1.0) -> None:
        super().__init__(filename)
        self.loaded.subscribe(partial(pygame.mixer.music.set_volume, volume))

    def play(self, repeat_count: int = REPEAT_FOREVER) -> None:
        self.ensure_loaded()
        pygame.mixer.music.play(loops=repeat_count)


class Font(Asset):
    def __init__(self, filename: str, size: int = 30) -> None:
        super().__init__(filename)
        self.load = lambda fname: pygame.font.Font(fname, size)
