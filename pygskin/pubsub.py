"""Publish-Subscribe pattern."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pygskin.utils import Decorator


class Message(Decorator):
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

    CANCEL = object()

    def __init__(self, callback: Callable | None = None, obj: Any = None) -> None:
        super().__init__(callback, obj=obj)
        self.subscribers: list[Callable] = []

    def call_function(self, *args, **kwargs) -> Any:
        """Publish the message."""
        cancelled = False
        for subscriber in self.subscribers:
            if not cancelled:
                cancelled = subscriber(*args, **kwargs) == Message.CANCEL
        if self.fn and not cancelled:
            self.fn(*args, **kwargs)

    def subscribe(self, subscriber: Callable) -> None:
        """Subscribe to the message."""
        self.subscribers.append(subscriber)


message = Message
