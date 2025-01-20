"""Module for defining remappable controls."""

from collections.abc import Callable
from functools import partial

from pygame.event import Event


def match_event(event: Event, other: Event) -> bool:
    """Return whether the given events match."""
    return event.type == other.type and event.__dict__.items() >= other.__dict__.items()


def get_action_mapper(mapping: dict[str, Event]) -> Callable[[Event], str | None]:
    """Return a function that maps input events to actions."""

    def get_action(event: Event) -> str | None:
        is_match = partial(match_event, event)
        for action, input_ in mapping.items():
            if input_ and is_match(input_):
                return action
        return None

    return get_action


def map_inputs_to_actions(mapping: dict[str, Event], events: list[Event]) -> list[str]:
    """Return a list of actions from the given events."""
    return list(filter(None, map(get_action_mapper(mapping), events)))
