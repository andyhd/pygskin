from collections.abc import Callable
from functools import partial

import pygame
import pygame.locals as pg
from pygame.event import Event

from pygskin import Direction
from pygskin import button
from pygskin import get_styles
from pygskin import label
from pygskin import radio
from pygskin import run_game
from pygskin import textfield
from pygskin.imgui import imgui

stylesheet = partial(
    get_styles,
    {
        "*": {
            "padding": [20],
            "spacing": 20,
            "align": "center",
            "valign": "middle",
            "grow": Direction.VERTICAL | Direction.HORIZONTAL,
        },
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
        "button": {
            "border_width": 1,
        },
        "button:hover": {
            "border_color": "green",
        },
        "radio": {
            "align": "left",
            "background_color": "#00ff0040",
        },
    },
)
gui = imgui(stylesheet)


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

        if any(e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE for e in events):
            exit()

        with gui(surface, events) as render:
            render(label(foo))
            render(textfield(bar), max_width=400)
            if render(button("Click me")):
                foo[:] = bar[:]

            with render.vertically():
                for text, value in choices.items():
                    if render(radio(text), checked=shared["choice"] == value):
                        print(f"You selected {text} ({value})")
                        shared["choice"] = value

            with render.horizontally():
                if render(button("Yes")):
                    print("You clicked Yes!")
                if render(button("No")):
                    print("You clicked No!")
                if render(button("Maybe")):
                    print("You clicked Maybe!")

    return _main


if __name__ == "__main__":
    run_game(pygame.Window("IMGUI Demo", (800, 600)), main())
