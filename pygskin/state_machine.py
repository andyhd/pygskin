from __future__ import annotations

from typing import Callable
from typing import Generic
from typing import Iterable
from typing import TypeVar

from pygskin import pubsub


Input = TypeVar("Input")
State = TypeVar("State")


class Transition(Generic[Input, State]):
    def __init__(
        self,
        to_state: State,
        input: Input = None,
        condition: Callable[[Input], bool] | None = None,
        callback: Callable[[Input], None] | None = None,
    ) -> None:
        self.to_state = to_state
        self.triggering_input = input
        self.condition = condition
        self.trigger = pubsub.Message()
        self.trigger.subscribe(callback)

    def is_triggered_by(self, input: Input) -> bool:
        return input == self.triggering_input or (
            isinstance(self.triggering_input, type)
            and type(input) == self.triggering_input
        )


class StateMachine(Generic[Input, State]):
    def __init__(self, transition_table: dict[State, Iterable], initial_state: State):
        self.transition_table = {
            state: [Transition(*t) for t in transitions]
            for state, transitions in transition_table.items()
        }
        self.initial_state = initial_state
        self.state = self.initial_state

    def next_state(self, input: Input) -> str:
        for t in self.transition_table[self.state]:
            if t.is_triggered_by(input) and (
                not callable(t.condition) or t.condition(input)
            ):
                t.trigger(input)
                self.state = t.to_state
                return self.state
        raise KeyError(f"No transition for {input}")
