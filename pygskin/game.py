"""A module for running a game loop with Pygame."""

from asyncio import run
from asyncio import sleep

import pygame
import pygame.constants
from pygame import Window
from pygame.event import get as get_events

from pygskin import Clock


def run_game(window: Window, fn, fps: int = 60):
    """
    Run a game loop with the given function.

    Args:
        window (pygame.Window): The window to run the game in.
        fn (Callable): The function to run each frame.
        fps (int): The frames per second to run the game at.
    """
    pygame.init()
    surface = window.get_surface()

    async def _main_loop():
        running = True
        quit_event_type = pygame.constants.QUIT

        def stop():
            nonlocal running
            running = False

        while running:
            Clock.tick(fps)
            events = get_events()
            for event in events:
                if event.type == quit_event_type:
                    stop()
            fn(surface, events, stop)
            window.flip()
            await sleep(0)

    run(_main_loop())
