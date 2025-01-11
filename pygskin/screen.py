from collections.abc import Callable
from contextlib import suppress
from typing import Any

import pygame
from pygame.event import Event

from pygskin.statemachine import statemachine


class ScreenManager:
    send: Callable
    quit: Callable


ScreenFn = Callable[[pygame.Surface, list[Event], ScreenManager], None]
Transition = Callable[[Any], ScreenFn | None]
TransitionTable = dict[ScreenFn, list[Transition]]


def screen_manager(transition_table: TransitionTable) -> Callable:
    sm = statemachine(transition_table)
    screen = [next(sm)]

    def send(input: Any) -> None:
        with suppress(StopIteration):
            screen[0] = sm.send(input)

    manager = ScreenManager()
    manager.send = send

    def _screen_manager(surface: pygame.Surface, events: list[Event], quit: Callable):
        manager.quit = quit
        screen[0](surface, events, manager)

    return _screen_manager

