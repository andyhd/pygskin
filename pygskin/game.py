import asyncio

import pygame
import pygame.locals as pg

from pygskin import Clock


def run_game(window: pygame.Window, fn, fps: int = 60):
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
        running = [True]
        quit = running.clear

        while running:
            Clock.tick(fps)
            events = list(pygame.event.get())
            if any(event.type == pg.QUIT for event in events):
                quit()
            fn(surface, events, quit)
            window.flip()
            await asyncio.sleep(0)

    asyncio.run(_main_loop())

