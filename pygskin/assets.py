from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any
from typing import Callable

import pygame
from ruamel.yaml import YAML

from pygskin.pubsub import message

AssetFilter = Callable[[Path], bool]


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

    def __init__(self, path: str | Path | None = None) -> None:
        match path:
            case Path():
                self.path = path
            case str():
                self.path = Path(path)
            case None:
                caller_path = Path(inspect.stack()[1].filename)
                if caller_path.is_file():
                    self.path = caller_path.parent / "assets"
                else:
                    self.path = Path("assets")
            case _:
                raise TypeError

        self.cache = {}

    @property
    def asset_class_by_suffix(self) -> dict[str]:
        return {ext: cls for cls in Asset.__subclasses__() for ext in cls.suffixes}

    @message
    def bulk_load_started(self, children: list[tuple[Path, int]]) -> None:
        pass

    @message
    def bulk_load_ended(self, children: list[tuple[Path, int]]) -> None:
        pass

    @message
    def asset_loaded(self, asset: Asset) -> None:
        pass

    def load(self, path: Path) -> Any:
        asset_class_by_suffix = self.asset_class_by_suffix

        if not path.is_file():
            for candidate in path.parent.glob(f"{path.stem}.*"):
                if candidate.suffix in asset_class_by_suffix:
                    path = candidate
                    break

        return asset_class_by_suffix[path.suffix].load(path)

    def load_all(self, filter_fn: AssetFilter | None = None) -> None:
        asset_class_by_suffix = self.asset_class_by_suffix
        children = list(
            filter(
                filter_fn,
                (
                    (f, f.stat().st_size)
                    for f in self.path.rglob("*")
                    if f.suffix in asset_class_by_suffix
                ),
            )
        )
        self.bulk_load_started(children=children)
        for child, _ in children:
            if child.is_dir():
                self.cache[child.name] = subdir = Assets(child)
                subdir.asset_loaded.subscribe(self.asset_loaded)
                subdir.load_all(filter_fn)
            else:
                self.cache[child.name] = asset = getattr(self, child.name)
                self.asset_loaded(asset)
        self.bulk_load_ended(children)

    def __getattr__(self, name: str) -> Any:
        if attr := self.__dict__.get(name):
            return attr

        if asset := self.cache.get(name):
            return asset

        path = self.path / name

        if path.is_dir():
            return self.cache.setdefault(name, Assets(path))

        return self.cache.setdefault(name, self.load(path))

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)


class Asset:
    @classmethod
    def load(cls, path: Path) -> Any:
        raise NotImplementedError


class Image(Asset):
    suffixes = [".gif", ".jpg", ".png"]

    @classmethod
    def load(cls, path: Path) -> pygame.Surface:
        pygame.display.init()
        return pygame.image.load(path).convert_alpha()


class Sound(Asset):
    suffixes = [".mp3", ".wav", ".ogg"]

    @classmethod
    def load(cls, path: Path) -> pygame.mixer.Sound:
        pygame.mixer.init()
        return pygame.mixer.Sound(path)

    @classmethod
    def stream(cls, path: Path) -> Any:
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        return pygame.mixer.music


class Font(Asset):
    suffixes = [".ttf"]

    class Font:
        def __init__(self, path: Path) -> None:
            self.path = path
            self.cache = {}

        def size(self, size: int = 30) -> pygame.font.Font:
            return self.cache.setdefault(
                size,
                pygame.font.Font(self.path, size),
            )

    @classmethod
    def load(cls, path: Path) -> Font.Font:
        pygame.font.init()
        return Font.Font(path)


class Yaml(Asset):
    suffixes = [".yaml", ".yml"]

    @classmethod
    def load(cls, path: Path) -> Any:
        return YAML(typ="safe").load(path)
