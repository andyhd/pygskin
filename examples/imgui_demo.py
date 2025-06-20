from collections.abc import Callable
from contextlib import contextmanager
from functools import partial

import pygame
from pygame.event import Event

from pygskin import IMGUI
from pygskin import button
from pygskin import get_styles
from pygskin import label
from pygskin import radio
from pygskin import run_game
from pygskin import textfield

stylesheet = partial(
    get_styles,
    {
        "label": {
            "color": "green",
            "font_size": 40,
        },
        "textfield": {
            "background_color": "white",
            "color": "black",
            "font_size": 30,
            "align": "left",
        },
        "button:hover": {
            "border_color": "green",
        },
    },
)
gui = IMGUI(stylesheet)


def main() -> Callable[[pygame.Surface, list[Event], Callable], None]:
    foo: list[str] = list("Hello, World!")
    bar: list[str] = list("Hello yourself!")
    choices: dict[str, int] = {
        "One": 1,
        "Two": 2,
        "Three": 3,
    }
    shared: dict = {"choice": 1}

    def _main(surface: pygame.Surface, events: list[Event], exit) -> None:
        surface.fill((0, 0, 0))

        with gui(surface, events) as render:
            render(label(foo), font_size=40, center=(400, 100))
            render(textfield(bar), size=(400, 50), center=(400, 200))
            if render(button("Click me"), size=(200, 50), center=(400, 300)):
                foo[:] = bar[:]

            def option(i: int, text: str, checked: bool):
                return render(radio(text), checked=checked, x=400, y=400 + 50 * i)

            for i, (text, value) in enumerate(choices.items()):
                if option(i, text, checked=shared["choice"] == value):
                    shared["choice"] = value

    return _main


if __name__ == "__main__":
    run_game(pygame.Window("IMGUI Demo", (800, 600)), main())
