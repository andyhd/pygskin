"""Publish-Subscribe pattern."""
from __future__ import annotations

from functools import partial
from typing import Any
from typing import Callable


class message:
    """
    A message that can be subscribed to.

    Can be used as an object:
    >>> msg = message()
    >>> msg.subscribe(lambda x: print(f"subscriber 1: {x}"))
    >>> msg.subscribe(lambda x: print(f"subscriber 2: {x}"))
    >>> msg("foo")
    subscriber 1: foo
    subscriber 2: foo

    Can also be used as a decorator:
    >>> @message
    ... def foo(x):
    ...     print(f"decorated: {x}")
    >>> foo.subscribe(lambda x: print(f"subscriber: {x}"))
    >>> foo("bar")
    subscriber: bar
    decorated: bar

    And a method decorator:
    >>> class Foo:
    ...     @message
    ...     def bar(self, x):
    ...         print(f"decorated: {x}")
    >>> foo = Foo()
    >>> foo.bar.subscribe(lambda x: print(f"subscriber: {x}"))
    >>> foo.bar("quux")
    subscriber: quux
    decorated: quux
    """

    def __init__(self, callback: Callable | None = None, obj: Any = None) -> None:
        self.callback = callback
        self.obj = obj
        self.subscribers: list[Callable] = []
        self.name: str | None = None

    def __call__(self, *args, **kwargs) -> None:
        """Publish the message."""
        for subscriber in self.subscribers:
            subscriber(*args, **kwargs)
        if self.callback:
            self.callback(*args, **kwargs)

    def __set_name__(self, owner: Any, name: str) -> None:
        self.name = name

    def __get__(self, obj: Any, obj_type: Any = None) -> message:
        if obj and obj != self.obj:
            msg = type(self)(partial(self.callback, obj), obj=obj)
            setattr(obj, self.name, msg)
            return msg
        return self

    def subscribe(self, subscriber: Callable) -> None:
        """Subscribe to the message."""
        self.subscribers.append(subscriber)
