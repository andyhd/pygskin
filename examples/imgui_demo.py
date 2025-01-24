from collections.abc import Callable
from contextlib import contextmanager
from functools import partial

import pygame
from pygame.event import Event

from pygskin import imgui
from pygskin.game import run_game
from pygskin.imgui import button
from pygskin.imgui import label
from pygskin.imgui import radio
from pygskin.imgui import textfield
from pygskin.stylesheet import get_styles

gui = imgui.IMGUI()
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


@contextmanager
def render_gui(surface: pygame.Surface, events: list[Event]):
    gui.events = events
    with imgui.render(gui, surface, stylesheet) as render:
        yield render


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

        with render_gui(surface, events) as gui:
            gui(label(foo), font_size=40, center=(400, 100))
            gui(textfield(bar), size=(400, 50), center=(400, 200))
            if gui(button("Click me"), size=(200, 50), center=(400, 300)):
                foo[:] = bar[:]

            def option(i: int, text: str, checked: bool):
                return gui(radio(text), checked=checked, x=400, y=400 + 50 * i)

            for i, (text, value) in enumerate(choices.items()):
                if option(i, text, checked=shared["choice"] == value):
                    shared["choice"] = value

    return _main


if __name__ == "__main__":
    run_game(pygame.Window("IMGUI Demo", (800, 600)), main())
