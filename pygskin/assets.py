from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any
from typing import Protocol

import pygame

from pygskin.pubsub import message


class Assets:
    """
    Assets provides attribute access to static assets in a directory.

    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as dirname:
    ...     data = bytes.fromhex('4749463839610100010000ff002c00000000010001000002003b')
    ...     with open(f"{dirname}/foo.gif", "wb") as f:
    ...         _ = f.write(data)
    ...     _ = pygame.init()
    ...     _ = pygame.display.set_mode((1, 1), pygame.HIDDEN)
    ...     Assets(Path(dirname)).foo.get_size()
    (1, 1)
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(__file__).parent / "assets"
        self.cache = {}
        self.load_started = message()
        self.asset_loaded = message()
        self.load_finished = message()

    def load(self) -> None:
        """Load all assets into cache."""
        children = [
            (f, f.stat().st_size)
            for f in Path(self.path).rglob("**/*")
            if self.is_recognised_asset(f)
        ]
        self.load_started(children=children)
        for child, size in children:
            if child.is_dir():
                subdir = Assets(child)
                subdir.asset_loaded.subscribe(self.asset_loaded)
                subdir.load()
                self.cache[child.name] = subdir
            else:
                self.cache[child.name] = Asset.load(child)
                self.asset_loaded(child)
        self.loaded = True
        self.load_finished()

    def __getattr__(self, name: str) -> Any:
        """Enable attribute access."""
        try:
            return self.cache[name]
        except KeyError:
            pass

        path = self.path / name
        if path.is_dir():
            return self.cache.setdefault(name, Assets(path))

        return self.cache.setdefault(name, Asset.load(path))

    def __getitem__(self, name: str) -> Any:
        return self.__getattr__(name)

    def is_recognised_asset(self, path: Path) -> bool:
        for asset_class in Asset.__subclasses__():
            if path.suffix in asset_class.suffixes:
                return True
        return False


class Asset(Protocol):
    class NotRecognisedError(Exception):
        pass

    @classmethod
    def load(cls, path: Path) -> Any:
        if not path.is_file():
            path = next(path.parent.glob(f"{path.stem}.*"))
        for asset_class in cls.__subclasses__():
            if path.suffix in asset_class.suffixes:
                return asset_class(path)

        raise cls.NotRecognisedError(path)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.data, name)


class Image(Asset):
    suffixes = [".gif", ".jpg", ".png"]

    def __init__(self, path: Path) -> None:
        pygame.display.init()
        self.data = pygame.image.load(path)


class Sound(Asset):
    suffixes = [".mp3", ".wav"]

    def __init__(self, path: Path) -> None:
        pygame.mixer.init()
        self.data = pygame.mixer.Sound(path)

    def play(self, *args, **kwargs) -> None:
        self.data.play(**kwargs)

    def stop(self) -> None:
        self.data.stop()

    def set_volume(self, value: float) -> None:
        self.data.set_volume(value)

    def fadeout(self, ms: int) -> None:
        self.data.fadeout(ms)


class Music(Sound):
    load = pygame.mixer.music.load

    REPEAT_FOREVER = -1

    def __init__(self, path: Path) -> None:
        pygame.mixer.init()
        pygame.mixer.music.load(path)

    def play(self, repeat_count: int = REPEAT_FOREVER, **kwargs) -> None:
        if not self._loaded:
            raise Music.NotLoaded(self.filename)
        if "loops" in kwargs:
            repeat_count = kwargs.pop("loops")
        pygame.mixer.music.play(loops=repeat_count, **kwargs)


class Font(Asset):
    suffixes = [".ttf"]

    def __init__(self, path: Path, size: int = 30) -> None:
        pygame.font.init()
        self.path = path

    @cache
    def size(self, size: int = 30) -> pygame.font.Font:
        return pygame.font.Font(self.path, size)
