from collections.abc import Generator
from collections.abc import MutableSequence
from dataclasses import dataclass
from typing import Callable
from typing import Generic
from typing import TypeVar

State = TypeVar("State")
Transition = Callable[..., State | None]


class TransitionTable(dict[State, MutableSequence[Transition]]):
    """A mapping of states to transitions."""


@dataclass
class StateMachine(Generic[State]):
    """A state machine implemented with a coroutine."""

    transition_table: TransitionTable
    state: State | None = None

    def __post_init__(self) -> None:
        self._statemachine = self._coro()
        next(self._statemachine)

    def _coro(self) -> Generator[State | None, tuple[tuple, dict], None]:
        if self.state is None:
            self.state = next(iter(self.transition_table))
        while self.state is not None:
            (args, kwargs) = yield self.state
            for transition in self.transition_table[self.state]:
                if next_state := transition(*args, **kwargs):
                    self.state = next_state
                    break

    def send(self, *args, **kwargs) -> State | None:
        """Send arguments to the state machine."""
        return self._statemachine.send((args, kwargs))
