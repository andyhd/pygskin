from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

import pygame


class Asset:
    """Base class for assets."""

    suffixes: set[str] = set()
    _class_by_suffix: dict[str, type[Asset]] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        Asset._class_by_suffix.update({suffix: cls for suffix in cls.suffixes})

    @classmethod
    def load(cls, path: Path) -> Any:
        raise NotImplementedError


class Assets(Asset):
    """
    Provides attribute access to static assets in a directory.

    >>> import tempfile
    >>> tempdir = tempfile.TemporaryDirectory()
    >>> Path(f"{tempdir.name}/foo.gif").write_bytes(
    ...     bytes.fromhex('4749463839610100010000ff002c00000000010001000002003b'))
    26
    >>> _ = pygame.init()
    >>> _ = pygame.display.set_mode((1, 1), pygame.HIDDEN)
    >>> Assets(tempdir.name).foo.get_size()
    (1, 1)
    """

    def __init__(self, path: str | Path | None = None) -> None:
        if path is None:
            # Find the path of the calling script.
            path = Path(inspect.stack()[1].filename).parent / "assets"
            if not path.is_file():
                path = Path("assets")
        self.path = Path(path)

    def __getattr__(self, name: str) -> Asset:
        """Load the asset with the given name."""
        matches = sorted(
            (
                path
                for path in self.path.glob(f"{name}*.*")
                if path.suffix in Asset._class_by_suffix
            ),
            key=lambda p: len(str(p)),
        )

        path = next(iter(matches), None)

        if path is None:
            raise AttributeError(f"Asset not found: {self.path / name}")

        if path.is_dir():
            asset = Assets(path)
        else:
            asset = Asset._class_by_suffix[path.suffix].load(path)

        setattr(self, name, asset)
        self.__annotations__[name] = type(asset)
        return asset

    def __getitem__(self, name: str) -> Asset:
        try:
            return getattr(self, name)
        except AttributeError as attr_error:
            raise KeyError(name) from attr_error

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def load_all(self) -> None:
        """Load all the assets in the directory."""
        for child in list(self.path.iterdir()):
            self[child.stem]


class Image(Asset):
    """An image asset."""

    suffixes = {".png", ".jpg", ".jpeg", ".gif"}

    @classmethod
    def load(cls, path: Path) -> pygame.Surface:
        pygame.display.init()
        return pygame.image.load(path)


class Sound(Asset):
    """A sound asset."""

    suffixes = {".wav", ".mp3", ".ogg"}

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
    """A font asset."""

    suffixes = {".ttf"}

    class _Font:
        def __init__(self, path: Path) -> None:
            self.path = path
            self.cache: dict[int, pygame.font.Font] = {}

        def size(self, size: int = 30) -> pygame.font.Font:
            return self.cache.setdefault(
                size,
                pygame.font.Font(self.path, size),
            )

    @classmethod
    def load(cls, path: Path) -> _Font:
        pygame.font.init()
        return Font._Font(path)


class YAML(Asset):
    """A YAML asset."""

    suffixes = {".yaml", ".yml"}

    @classmethod
    def load(cls, path: Path) -> Any:
        import yaml

        return yaml.safe_load(path.read_text())
