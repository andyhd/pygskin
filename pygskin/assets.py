import inspect
import json
from collections import UserDict
from collections.abc import Callable
from collections.abc import Iterator
from functools import cache
from pathlib import Path
from typing import Any

import pygame

type Asset = Any  # type: ignore


def load_font(path: Path):
    return cache(lambda size=30: pygame.font.Font(path, size))


def load_json(path: Path):
    return json.loads(path.read_text())


def load_yaml(path: Path):
    import yaml

    return yaml.safe_load(path.read_text())


LOADERS: dict[str, Callable] = {
    **{_: pygame.image.load for _ in {".png", ".jpg", ".jpeg", ".gif"}},
    **{_: pygame.mixer.Sound for _ in {".wav", ".mp3", ".ogg"}},
    **{_: load_font for _ in {".ttf"}},
    **{_: load_yaml for _ in {".yaml", ".yml"}},
    **{_: load_json for _ in {".json"}},
}


def get_assets_path_from_caller_frame() -> Path:
    try:
        return Path(inspect.stack()[2].filename).parent / "assets"
    except IndexError:
        return Path("assets")


def find_assets_by_name(path: Path, name: str) -> Iterator[Path]:
    yield from sorted(
        (m for m in path.glob(f"{name}*.*") if m.suffix in LOADERS),
        # shortest match first
        key=lambda _: len(str(_)),
    )


def get_asset(path: Path, name: str) -> Asset:
    match next(find_assets_by_name(path.parent, name), None):
        case Path() as p if p.is_dir():
            asset = Assets(p)
        case Path() as p:
            asset = LOADERS[p.suffix](p)
        case None:
            raise LookupError(f"Asset not found: {path / name}")
    return asset


class Assets(UserDict):
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
        super().__init__()
        match path:
            case Path():
                ...
            case str(s):
                path = Path(s)
            case None:
                path = get_assets_path_from_caller_frame()
            case _:
                raise TypeError(f"Expected Path or str, got {type(path)}")
        if not path.is_dir():
            raise ValueError(f"Path does not exist: {path}")
        self.__dict__["path"] = path

    def __getitem__(self, name: str) -> Asset:
        if not (asset := self.data.get(name)):
            try:
                asset = self.data[name] = get_asset(self.__dict__["path"] / name, name)
            except LookupError as e:
                raise KeyError(name) from e
        return asset

    def __getattr__(self, name: str) -> Asset:
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError from e

    def load_all(self) -> None:
        for child in list(self.path.iterdir()):
            self[child.stem]
