from __future__ import annotations

import inspect
import typing
from typing import Any

import pygame
from pygame.event import Event

from pygskin.statemachine import StateMachine
from pygskin.statemachine import TransitionTable


class Screen:
    def __init__(self, manager: ScreenManager) -> None:
        self.manager = manager
        self.setup()

    def exit(self, output: Any = None) -> None:
        self.manager.show_next(output)

    def setup(self) -> None:
        ...

    def update(self, events: list[Event]) -> None:
        ...

    def draw(self, surface: pygame.Surface) -> None:
        ...


class ScreenManager:
    def __init__(self, initial: type[Screen]) -> None:
        self.initial = initial

        transition_table = TransitionTable[type[Screen]]()
        screens = [initial]

        while screens:
            screen = screens.pop()
            for _, attr in inspect.getmembers(screen, callable):
                if (
                    (type_hints := typing.get_type_hints(attr, include_extras=True))
                    and (type_hint := type_hints.get("return"))
                    and typing.get_origin(type_hint) is type
                    and (screen_type := next(iter(typing.get_args(type_hint)), None))
                    and issubclass(screen_type, Screen)
                ):
                    transition_table.setdefault(screen, []).append(attr)
                    if not any(
                        key.__name__ == screen_type.__name__ for key in transition_table
                    ):
                        screens.append(screen_type)

        self.statemachine = StateMachine[type[Screen]](transition_table)
        self.screen = self.initial(self)

    def update(self, events: list[Event]) -> None:
        self.screen.update(events)

    def draw(self, surface: pygame.Surface) -> None:
        self.screen.draw(surface)

    def show_next(self, output: object | None = None) -> None:
        self.statemachine.send(output)
        next_screen = self.statemachine.state
        if next_screen is not None and next_screen != self.screen.__class__:
            self.screen = next_screen(self)
