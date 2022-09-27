from __future__ import annotations

import sys
from inspect import Signature
from typing import Callable

from pygskin.events import Event
from pygskin.events import Quit
from pygskin.interfaces import Updatable
from pygskin.timer import Timer


class Input:
    def __init__(self, handler: Callable, *args, **kwargs) -> None:
        self.handler = handler

        params = Signature.from_callable(handler).bind(*args, **kwargs)
        params.apply_defaults()

        self.args = params.args
        self.kwargs = params.kwargs

    def execute(self) -> None:
        self.handler(*self.args, **self.kwargs)


class InputHandler(Updatable):
    event_map: dict[Event, Input]

    def get_input_for_event(self, event: Event) -> Input | None:
        input = next(
            (input for ev, input in self.event_map.items() if ev == event), None
        )
        if input is None:
            if isinstance(event, Timer):
                input = Input(self.timer, event)
            elif isinstance(event, Quit):
                sys.exit(0)
        if isinstance(input, str):
            input = Input(input)
        return input

    def get_inputs(self) -> list[Input]:
        return [
            input
            for input in map(self.get_input_for_event, Event.queue)
            if input is not None
        ]

    def update(self, _: float) -> None:
        for input in self.get_inputs():
            input.execute()

    def timer(self, timer: Timer) -> None:
        timer.finish()
