"""Example of a simple game with a main menu and a play screen."""

import random
from collections.abc import Callable
from functools import cache

import pygame
import pygame.locals as pg
from pygame import Color
from pygame import Surface
from pygame import Vector2
from pygame.color import THECOLORS
from pygame.event import Event

from pygskin import Clock
from pygskin import Entity
from pygskin import imgui
from pygskin import run_game
from pygskin import screen_manager
from pygskin import system
from pygskin.imgui import button
from pygskin.imgui import label
from pygskin.imgui import textfield

gui = imgui.IMGUI()
shared: dict = {"buffer": list("10000"), "num_balls": "10000"}


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


class Ball(Entity):
    """A simple ball sprite."""

    position: Vector2 = lambda: Vector2(random.randint(0, 800), random.randint(0, 600))
    velocity: Vector2 = lambda: Vector2(random.uniform(-6, 6), random.uniform(-6, 6))

    def __init__(self) -> None:
        super().__init__()
        self.image = Surface((10, 10), pg.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(
            self.image,
            Color(random.choice(list(THECOLORS.keys()))),
            (5, 5),
            5,
        )


@system
def apply_velocity(position: Vector2, velocity: Vector2) -> None:
    """Apply velocity to entities."""
    position += velocity
    position.x %= 800
    position.y %= 600


@cache
def play_game():
    """
    Return the play game screen function.
    """
    balls = []

    def _play(surface: Surface, events: list[Event], exit_screen: Callable) -> None:
        if not balls:
            balls.extend(Ball() for _ in range(int(shared["num_balls"])))

        surface.fill((0, 0, 0))

        apply_velocity()

        surface.blits([(ball.image, ball.position) for ball in balls])

        with imgui.render(gui, surface) as render:
            render(label(f"FPS: {Clock.get_fps():.1f}"), font_size=30, topleft=(10, 10))
        
    return _play


if __name__ == "__main__":
    run_game(pygame.Window("Testing", (800, 600)), main(), fps=0)
