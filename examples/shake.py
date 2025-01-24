"""Shake animation example"""

from collections.abc import Callable

import pygame
import pygame.locals as pg
from pygame import Event
from pygame import Rect
from pygame import Surface
from pygame import Window

from pygskin import ScreenFn
from pygskin import Timer
from pygskin import animate
from pygskin import run_game
from pygskin import shake


def shake_example() -> ScreenFn:
    """Shake animation example."""

    rect = Rect(350, 250, 100, 100)
    timer = Timer(3000)
    shake_anim = animate(shake(), timer.quotient)

    def main_loop(screen: Surface, events: list[Event], exit: Callable) -> None:
        nonlocal shake_anim

        screen.fill("black")
        timer.tick()
        pygame.draw.rect(screen, "red", rect.move(next(shake_anim)))

        if any(event.type == pg.KEYDOWN for event in events):
            timer.elapsed = 0
            shake_anim = animate(shake(), timer.quotient)

    return main_loop


if __name__ == "__main__":
    run_game(Window("Camera shake", (800, 600)), shake_example())
