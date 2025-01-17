"""Screen manager for Pygame applications."""

from collections.abc import Callable
from contextlib import suppress
from typing import Any

from pygame import Surface
from pygame.event import Event

from pygskin.statemachine import statemachine

ScreenFn = Callable[[Surface, list[Event], Callable], None]
Transition = Callable[[Any], ScreenFn | None]
TransitionTable = dict[ScreenFn, list[Transition]]
EXIT = object()


def screen_manager(*screens: ScreenFn) -> Callable:
    """Return a screen manager function."""

    def transition_screen(to: ScreenFn) -> ScreenFn | None:
        if to not in screens:
            raise ValueError(f"Transition to unknown screen: {to}")
        return to

    sm = statemachine({screen: [transition_screen] for screen in screens})
    screen = next(sm)

    def exit_manager(*_) -> None:
        raise ValueError("exit_manager not set")

    def exit_screen(to: Transition | None = None) -> None:
        nonlocal screen
        if to is None:
            exit_manager()
            return
        with suppress(StopIteration):
            screen = sm.send(to)

    def _screen_manager(surface: Surface, events: list[Event], exit_: Callable):
        nonlocal exit_manager
        exit_manager = exit_
        screen(surface, events, exit_screen)

    return _screen_manager
