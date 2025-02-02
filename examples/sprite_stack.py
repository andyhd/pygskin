from collections.abc import Callable

from pygame import Event
from pygame import Surface
from pygame import Vector2
from pygame import Window
from pygame.transform import scale_by

from pygskin import Assets
from pygskin import draw_sprite_stack
from pygskin import run_game
from pygskin import spritesheet

assets = Assets()


def sprite_stacking_demo() -> Callable:
    frog = spritesheet(scale_by(assets.frog, 4), rows=1, columns=11)
    pos = Vector2(200, 200)
    angle = 0

    def main_loop(surface: Surface, events: list[Event], exit_: Callable) -> None:
        nonlocal angle

        surface.fill("aqua")

        draw_sprite_stack(surface, frog, pos, angle, 4)

        angle += 1

    return main_loop


if __name__ == "__main__":
    run_game(Window("Sprite Stacking Demo", (400, 400)), sprite_stacking_demo())
