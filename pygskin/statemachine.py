from collections.abc import Callable
from collections.abc import Generator
from typing import Any

RESET = object()


def statemachine(
    transition_table: dict[Any, list[Callable]],
) -> Generator[Any, Any, None]:
    """
    A state machine implemented with a coroutine.

    >>> s = {"code": [1, 2, 3], "buffer": []}
    >>> def unlock(i):
    ...     buffer = s["buffer"] + [i]
    ...     if buffer == s["code"]:
    ...         return "unlocked"
    >>> def error(i):
    ...     buffer = s["buffer"] + [i]
    ...     if len(buffer) == len(s["code"]) and buffer != s["code"]:
    ...         return lock()
    >>> def digit(i):
    ...     if isinstance(i, int) and 0 <= i <= 9:
    ...         s["buffer"].append(i)
    ...         return "entering_code"
    >>> def lock(*_):
    ...     s["buffer"].clear()
    ...     return "locked"
    >>> safe = statemachine({
    ...     "locked": [digit],
    ...     "entering_code": [unlock, error, digit],
    ...     "unlocked": [lock],
    ... })
    >>> next(safe)
    'locked'
    >>> safe.send('A')
    'locked'
    >>> safe.send(5)
    'entering_code'
    >>> safe.send(5)
    'entering_code'
    >>> safe.send(5)
    'locked'
    >>> safe.send(1)
    'entering_code'
    >>> safe.send(2)
    'entering_code'
    >>> safe.send(3)
    'unlocked'
    """

    state = next(iter(transition_table))
    while state:
        input = yield state
        if input is RESET:
            state = next(iter(transition_table))
            yield None
            continue
        for transition in transition_table[state]:
            if next_state := transition(input):
                state = next_state
                break


statemachine.RESET = RESET  # type: ignore
