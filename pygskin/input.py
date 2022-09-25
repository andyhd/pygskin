from __future__ import annotations

from types import MethodType
from typing import Callable

from pygskin.events import Event
from pygskin.interfaces import Updatable


class InputHandler(Updatable):
    event_map: dict[Event, str]

    def get_input_for_event(self, event: Event) -> str | None:
        return self.event_map.get(event)

    def get_inputs(self) -> list[str]:
        return list(
            filter(
                None,
                (self.event_map.get(event) for event in Event.queue),
            )
        )

    def handle_input(self, input: str) -> None:
        try:
            return getattr(self, input)()
        except AttributeError:
            pass

    def update(self, _: float) -> None:
        for input in self.get_inputs():
            self.handle_input(input)


class input:
    def __init__(self, fn: Callable | None = None, **kwargs) -> None:
        self.fn = fn
        self.options = kwargs

    def __set_name__(self, owner_class: type, name: str) -> None:
        if not hasattr(owner_class, "_input_handlers"):
            setattr(owner_class, "_input_handlers", {})
        getattr(owner_class, "_input_handlers").setdefault(name, []).append(self.fn)

    def __get__(self, instance, _=None) -> input | MethodType:
        if instance and callable(self.fn):
            return MethodType(self.fn, instance)
        return self

    def __call__(self, fn: Callable) -> input | None:
        if self.fn is None and callable(fn):
            self.fn = fn
            return self
