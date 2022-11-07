from __future__ import annotations

from inspect import Signature
from typing import Callable

from pygskin.events import Event
from pygskin.events import Quit
from pygskin.interfaces import Updatable
from pygskin.timer import Timer


class Input:
    def __init__(self, handler: Callable, *args, **kwargs) -> None:
        self.handler = handler
        self.args = args
        self.kwargs = kwargs

    def execute(self) -> None:
        params = Signature.from_callable(self.handler).bind(*self.args, **self.kwargs)
        params.apply_defaults()
        self.handler(*params.args, **params.kwargs)


class InputHandler(Updatable):
    event_map: dict[Event, Input]

    def get_input_for_event(self, event: Event) -> Input | None:
        input = next(
            (
                input
                for ev, input in getattr(self, "event_map", {}).items()
                if ev == event
            ),
            None,
        )
        if input is None:
            if isinstance(event, Timer):
                input = Input(self.timer, event)
            elif isinstance(event, Quit):
                getattr(self, "quit", lambda _: None)()
        if isinstance(input, str):
            input = Input(getattr(self, input))
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
