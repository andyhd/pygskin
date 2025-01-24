"""Example of a simple game with a main menu and a play screen."""

import random
from collections.abc import Callable
from functools import cache

import pygame
import pygame.locals as pg
from pygame import Color
from pygame import FRect
from pygame import Surface
from pygame import Vector2
from pygame.color import THECOLORS
from pygame.event import Event
from pygame.sprite import Group
from pygame.sprite import Sprite

from pygskin import get_ecs_update_fn
from pygskin import imgui
from pygskin import run_game
from pygskin import screen_manager
from pygskin.imgui import button
from pygskin.imgui import label
from pygskin.imgui import textfield

gui = imgui.IMGUI()
shared: dict = {"buffer": list("1000"), "num_balls": "1000"}


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


class Ball(Sprite):
    """
    A simple ball sprite.
    """

    def __init__(self) -> None:
        super().__init__()
        self.vel = Vector2(random.uniform(-6, 6), random.uniform(-6, 6))
        self.image = Surface((10, 10)).convert_alpha()
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(
            self.image,
            Color(random.choice(list(THECOLORS.keys()))),
            (5, 5),
            5,
        )
        self.rect = FRect(
            self.image.get_rect(
                centerx=random.randint(0, 800),
                centery=random.randint(0, 600),
            )
        )


def move(ball: Ball, *_, **__) -> None:
    """
    Move the ball sprite.
    """
    if ball.rect is not None:
        new_pos = ball.rect.topleft + ball.vel
        ball.rect.x = new_pos.x % 800.0
        ball.rect.y = new_pos.y % 600.0


@cache
def play_game():
    """
    Return the play game screen function.
    """
    ecs_update = get_ecs_update_fn([move])
    entities = Group()

    def _play(surface: Surface, events: list[Event], exit_screen: Callable) -> None:
        if not entities:
            entities.add(*(Ball() for _ in range(shared["num_balls"])))

        ecs_update(entities)

        surface.fill((0, 0, 0))
        entities.draw(surface)

        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    exit_screen()

                else:
                    exit_screen(to=main_menu)

    return _play


if __name__ == "__main__":
    run_game(pygame.Window("Testing", (800, 600)), main())
