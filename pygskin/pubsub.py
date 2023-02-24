"""Publish-Subscribe pattern."""

from functools import partial
from typing import Any
from typing import Callable


class message:
    """
    A message that can be subscribed to.
    """

    def __init__(self, callback: Callable | None = None, obj: Any = None) -> None:
        self.callback = callback
        self.obj = obj
        self.subscribers: list[Callable] = []
        self.name = None

    def __call__(self, *args, **kwargs):
        """Publish the message."""
        for subscriber in self.subscribers:
            subscriber(*args, **kwargs)
        if self.obj:
            self.callback(*args, **kwargs)

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, obj_type=None):
        if obj and obj != self.obj:
            msg = type(self)(partial(self.callback, obj), obj=obj)
            setattr(obj, self.name, msg)
            return msg
        return self

    def subscribe(self, subscriber):
        """Subscribe to the message."""
        self.subscribers.append(subscriber)
