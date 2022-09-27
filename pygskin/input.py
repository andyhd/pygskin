from __future__ import annotations

from inspect import Signature
from types import MethodType
from typing import Callable

from pygskin.events import Event
from pygskin.interfaces import Updatable
from pygskin.timer import Timer


class Input:
    def __init__(self, handler_name: str, *args, **kwargs) -> None:
        self.handler_name = handler_name
        self.args = args
        self.kwargs = kwargs


class input_handler:
    def __init__(self, fn: Callable | None = None) -> None:
        self.fn = fn

    def __set_name__(self, owner_class: type, name: str) -> None:
        if not hasattr(owner_class, "_input_handlers"):
            setattr(owner_class, "_input_handlers", {})
        getattr(owner_class, "_input_handlers").setdefault(name, []).append(self.fn)

    def __get__(self, instance, _=None) -> input_handler | MethodType:
        if instance and callable(self.fn):
            return MethodType(self.fn, instance)
        return self

    def __call__(self, fn: Callable) -> input_handler | None:
        if self.fn is None and callable(fn):
            self.fn = fn
            return self


class InputHandler(Updatable):
    event_map: dict[Event, Input]

    def get_input_for_event(self, event: Event) -> Input | None:
        input = self.event_map.get(event)
        if input is None and isinstance(event, Timer):
            input = Input("timer", event)
        if isinstance(input, str):
            input = Input(input)
        return input

    def get_inputs(self) -> list[Input]:
        return [
            input
            for input in map(self.get_input_for_event, Event.queue)
            if input is not None
        ]

    def handle_input(self, input: Input) -> None:
        try:
            handler = getattr(self, input.handler_name)
        except AttributeError:
            return None

        params = Signature.from_callable(handler).bind(*input.args, **input.kwargs)
        params.apply_defaults()

        return handler(*params.args, **params.kwargs)

    def update(self, _: float) -> None:
        for input in self.get_inputs():
            self.handle_input(input)

    @input_handler
    def timer(self, timer: Timer) -> None:
        timer.finish()
