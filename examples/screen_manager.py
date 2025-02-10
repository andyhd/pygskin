"""Example of a simple game with a main menu and a play screen."""

import random
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache

import pygame
import pygame.locals as pg
from pygame import Color
from pygame import Surface
from pygame import Vector2
from pygame.color import THECOLORS
from pygame.event import Event

from pygskin import Component
from pygskin import imgui
from pygskin import run_game
from pygskin import screen_manager
from pygskin.imgui import button
from pygskin.imgui import label
from pygskin.imgui import textfield

gui = imgui.IMGUI()
shared: dict = {"buffer": list("1000"), "num_balls": "1000"}


class Position(Component[Vector2]): ...


class Velocity(Component[Vector2]): ...


def main():
    """
    Return a screen manager for the main menu and game screens.
    """
    return screen_manager(
        main_menu,
        play_game(),
    )


def main_menu(surface: Surface, events: list[Event], exit_screen: Callable) -> None:
    """
    Display the main menu screen.
    """
    surface.fill((0, 0, 0))
    gui.events = events
    with imgui.render(gui, surface) as render:
        render(label("Main Menu"), font_size=40, center=(400, 100))

        render(textfield(shared["buffer"]), size=(200, 50), center=(400, 200))

        if render(button("Start Game"), size=(200, 50), center=(400, 300)):
            shared["num_balls"] = int("".join(shared["buffer"]))
            exit_screen(to=play_game())


@dataclass
class Ball:
    """A simple ball sprite."""

    position: Position = Position()
    velocity: Velocity = Velocity()

    def __post_init__(self) -> None:
        self.image = Surface((10, 10), pg.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(
            self.image,
            Color(random.choice(list(THECOLORS.keys()))),
            (5, 5),
            5,
        )
        self.position = Vector2(random.randint(0, 800), random.randint(0, 600))
        self.velocity = Vector2(random.uniform(-6, 6), random.uniform(-6, 6))


def apply_velocity() -> None:
    """Apply velocity to entities."""
    for id, vel in Velocity.components.items():
        pos = Position.components[id]
        pos += vel
        pos.x %= 800
        pos.y %= 600


@cache
def play_game():
    """
    Return the play game screen function.
    """
    entities = [Ball() for _ in range(int(shared["num_balls"]))]

    def _play(surface: Surface, events: list[Event], exit_screen: Callable) -> None:
        apply_velocity()

        surface.fill((0, 0, 0))
        surface.blits((ball.image, ball.position) for ball in entities)

        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    exit_screen()

                else:
                    exit_screen(to=main_menu)

    return _play


if __name__ == "__main__":
    run_game(pygame.Window("Testing", (800, 600)), main())
