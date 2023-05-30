from dataclasses import dataclass, field
from typing import Callable
from typing import Iterator
from typing import TypeVar

from pygskin.pubsub import message

Input = TypeVar("Input")
State = TypeVar("State")
Transition = Callable[[Input], State | None]
TransitionTable = dict[State, list[Transition]]


@dataclass
class StateMachine:
    """
    A state machine implemented with a coroutine

    >>> s = {"code": [1, 2, 3], "buffer": []}
    >>> def unlock(i):
    ...     buffer = s["buffer"] + [i]
    ...     if len(buffer) == len(s["code"]) and buffer == s["code"]:
    ...         return "unlocked"
    >>> def error(i):
    ...     buffer = s["buffer"] + [i]
    ...     if len(buffer) == len(s["code"]) and not buffer == s["code"]:
    ...         return lock()
    >>> def digit(i):
    ...     if isinstance(i, int) and 0 <= i <= 9:
    ...         s["buffer"].append(i)
    ...         return "entering_code"
    >>> def lock(*_):
    ...     s["buffer"].clear()
    ...     return "locked"
    >>> safe = StateMachine(
    ...     {
    ...         "locked": [digit],
    ...         "entering_code": [unlock, error, digit],
    ...         "unlocked": [lock],
    ...     },
    ... )
    >>> safe.state
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

    transition_table: TransitionTable
    state: State | None = None

    def __post_init__(self) -> None:
        self.started = message()
        self.received_input = message()
        self.triggered = message()
        self.not_triggered = message()
        self._statemachine = self._coro()
        next(self._statemachine)

    def _coro(self) -> Iterator[State | None]:
        self.started()
        if self.state is None:
            self.state = next(iter(self.transition_table))
        while self.state:
            input = yield self.state
            self.received_input(input)
            for transition in self.transition_table[self.state]:
                if next_state := transition(input):
                    self.triggered(input, self.state, next_state)
                    self.state = next_state
                    break
            else:
                self.not_triggered(input, self.state)

    def send(self, *args, **kwargs) -> State | None:
        return self._statemachine.send(*args, **kwargs)
