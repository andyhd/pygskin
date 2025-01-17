"""Publish-Subscribe pattern."""

from collections.abc import Callable
from functools import wraps
from typing import Any

CANCEL = object()


def channel(fn: Callable | None = None) -> Callable:
    """
    Returns message channel that can be subscribed to.

    Can be used as an object:
    >>> foo = channel()
    >>> foo.subscribe(lambda x: print(f"subscriber 1: {x}"))
    >>> foo.subscribe(lambda x: print(f"subscriber 2: {x}"))
    >>> foo("bar")
    subscriber 1: bar
    subscriber 2: bar

    Can also be used as a decorator:
    >>> @channel
    ... def foo(x):
    ...     print(f"decorated: {x}")
    >>> foo.subscribe(lambda x: print(f"subscriber: {x}"))
    >>> foo("bar")
    subscriber: bar
    decorated: bar

    And a method decorator:
    >>> class Foo:
    ...     @channel
    ...     def bar(self, x):
    ...         print(f"decorated: {x}")
    >>> foo = Foo()
    >>> foo.bar.subscribe(lambda self, x: print(f"subscriber: {x}"))
    >>> foo.bar("quux")
    subscriber: quux
    decorated: quux

    A message can be cancelled by returning `message.cancel` from a subscriber:
    >>> foo = channel()
    >>> foo.subscribe(lambda x: print(f"subscriber 1: {x}") or foo.cancel)
    >>> foo.subscribe(lambda x: print(f"subscriber 2: {x}"))
    >>> foo("bar")
    subscriber 1: bar
    """

    subscribers: list[Callable] = []

    def subscribe(subscriber: Callable) -> None:
        """Subscribe to the message."""
        subscribers.append(subscriber)

    def wrapper(*args, **kwargs) -> Any:
        """Publish the message."""
        cancel = CANCEL
        for subscriber in subscribers:
            if subscriber(*args, **kwargs) == cancel:
                break
        else:
            if fn:
                fn(*args, **kwargs)

    if fn:
        wrapper = wraps(fn)(wrapper)

    wrapper.subscribe = subscribe  # type: ignore
    wrapper.cancel = CANCEL  # type: ignore

    return wrapper
