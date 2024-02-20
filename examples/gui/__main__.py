"""GUI example."""

from __future__ import annotations

import random

import pygame

from pygskin import gui
from pygskin import layout as layout_
from pygskin.assets import Assets
from pygskin.direction import Direction
from pygskin.display import Display
from pygskin.utils import make_sprite
from pygskin.window import Window

assets = Assets()


ALL_COLORS = [(k, pygame.Color(v)) for k, v in pygame.colordict.THECOLORS.items()]


class Toolbar(gui.Container):
    """Toolbar widget."""

    def __init__(
        self,
        direction: Direction = Direction.HORIZONTAL,
        size: tuple[int, int] | None = None,
        layout: layout_.Layout | None = None,
        **kwargs,
    ) -> None:
        """Construct instance."""
        super().__init__(**kwargs)
        if size:
            self.rect = pygame.Rect((0, 0), size)
        self.layout: layout_.Layout = layout or layout_.Fill(direction=direction)


class Game(Window):
    """Game window."""

    def __init__(self) -> None:
        """Construct the instance."""
        super().__init__(size=(800, 600), title="GUI")

        root = gui.Root()

        regions: dict[str, pygame.sprite.Sprite] = {
            "north": Toolbar(Direction.HORIZONTAL, size=(800, 50)),
            "south": Toolbar(Direction.HORIZONTAL, size=(800, 50)),
            "west": Toolbar(Direction.VERTICAL, size=(100, 600)),
            "east": Toolbar(Direction.VERTICAL, size=(100, 600)),
            "center": make_sprite(assets.center),
        }

        for name, child in regions.items():
            if hasattr(child, "add_child"):
                for i in range(8 if name in ("north", "south") else 10):
                    name, color = random.choice(ALL_COLORS)
                    child.add_child(
                        gui.Button(
                            f"btn{i}",
                            style={
                                "align": "CENTER",
                                "background": color,
                                "color": "black" if color.hsla[2] > 50 else "white",
                                "padding": [20],
                            },
                        )
                    )
            root.add_child(child)

        root.layout = layout_.Border(**regions)
        Display.sprites.add(root)


if __name__ == "__main__":
    Game().run()
