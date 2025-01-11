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


def screen_manager(transition_table: TransitionTable) -> Callable:
    sm = statemachine(transition_table)

    manager = {
        "screen": next(sm),
    }

    def send(input: Any = EXIT) -> None:
        if input == EXIT:
            manager["exit"]()
            return
        with suppress(StopIteration):
            manager["screen"] = sm.send(input)

    def _screen_manager(surface: Surface, events: list[Event], exit: Callable):
        manager.setdefault("exit", exit)
        manager["screen"](surface, events, send)

    return _screen_manager

