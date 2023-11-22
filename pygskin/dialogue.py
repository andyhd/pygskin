"""Dialogue as nested state machine."""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import InitVar
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import TypedDict

from pygskin.clock import Timer
from pygskin.events import CustomEvent
from pygskin.events import event_listener
from pygskin.pubsub import message
from pygskin.statemachine import StateMachine
from pygskin.statemachine import TransitionTable

log = logging.getLogger(__name__)


class Context(dict[str, Any]):
    def eval(self, expr: str, **extra) -> Any:
        return eval(str(expr), {}, dict(**self, **extra))

    def eval_update(self, assignments: dict[str, Any], **extra) -> None:
        for var, expr in assignments.items():
            self[var] = self.eval(expr, **extra)


@dataclass
class SceneTransition:
    def __call__(self, context: Context) -> str | None:
        return context.pop("next_state", None)


@dataclass
class Dialogue(StateMachine):
    context: Context | None = None
    transition_table: TransitionTable = field(default_factory=dict)
    scenes: dict[str, Scene] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.transition_table = {}

        for name, scene in self.scenes.items():
            self.transition_table.setdefault(name, []).append(SceneTransition())
            scene.end.subscribe(self.next_scene)
            scene.state_changed.subscribe(self.action_changed)

        super().__post_init__()

    @classmethod
    def load(cls, data: dict) -> Dialogue:
        context = Context(data.pop("context", {}))
        scenes = {name: Scene(context=context, actions=_) for name, _ in data.items()}

        return Dialogue(scenes=scenes, context=context)

    @property
    def scene(self) -> Scene:
        return self.scenes[self.state]

    def update(self) -> None:
        self.scene.update()

    def next_scene(self, next_scene: str | None = None) -> None:
        if next_scene:
            if next_scene == "end":
                return self.end()
            self.context["next_state"] = next_scene
        self.send(self.context)
        self.update()

    @message
    def end(self) -> None:
        pass

    @message
    def action_changed(self) -> None:
        pass


@dataclass
class Transition:
    next_state: Any
    condition: str | None = None

    def __call__(self, context: Context) -> Any:
        if self.condition is None or context.eval(self.condition):
            return self.next_state
        return None


@dataclass
class Scene(StateMachine):
    context: Context = field(default_factory=Context)
    transition_table: TransitionTable = field(default_factory=dict)
    actions: InitVar[list[dict[str, Any]]] = None

    def __post_init__(self, actions: list[dict[str, Any]]) -> None:
        self.actions = [Action.build(_, self.context) for _ in actions]

        prev = None
        branch_start = None
        branch_end = None
        for i, action in enumerate(self.actions):
            self.transition_table.setdefault(i, [])
            action.end.subscribe(self.next_action)

            if prev is not None:
                transitions = self.transition_table[prev]
                if action.trigger is None:
                    if branch_start is not None:
                        branch_end.next_state = i
                        branch_end = None
                        branch_start = None
                    transitions.append(Transition(next_state=i))
                else:
                    if branch_start is None:
                        branch_start = prev
                        branch_end = Transition(next_state=None)
                    self.transition_table[branch_start].insert(
                        len(self.transition_table[branch_start]) - 1,
                        Transition(next_state=i, condition=action.trigger),
                    )
                    transitions.append(branch_end)

            prev = i

        super().__post_init__()

    @property
    def action(self) -> Action:
        return self.actions[self.state]

    def update(self) -> None:
        self.action.update()

    @message
    def end(self, next_state: str | None) -> None:
        self.state = next(iter(self.transition_table))

    def next_action(self, next_state: str | None = None) -> None:
        if next_state:
            return self.end(next_state)
        self.send(self.context)
        self.update()


def capwords(snakecase: str) -> str:
    return "".join(word.capitalize() for word in snakecase.split("_"))


@dataclass
class Action:
    trigger: str | None = field(repr=False)
    context: Context = field(repr=False, compare=False)

    @classmethod
    def build(cls, data: dict[str, Any], context: Context) -> Action:
        args = [data.pop("if", None), context]
        name, data = data.popitem()
        subclasses = {subclass.__name__: subclass for subclass in cls.__subclasses__()}

        if action_class := subclasses.get(capwords(name)):
            return action_class(*args, *[data])

        match data:
            case {"animation": str(animation)}:
                return Animate(*args, *[name, animation])
            case str(line):
                return Say(*args, *[name, line])
            case _:
                raise ValueError(f"{name} not a recognised Action")

    def update(self) -> None:
        pass

    @message
    def end(self, next_state: str | None = None) -> None:
        pass


@dataclass
class UpdateContext(Action):
    assignments: dict[str, Any]

    def update(self) -> None:
        self.context.eval_update(self.assignments)
        log.info(self.context)
        self.end()


class Timed:
    def update(self) -> None:
        if not hasattr(self, "timer"):
            self.timer = Timer(self.duration, on_expire=self.timer_end, delete=True)
            self.timer.start()

    def timer_end(self) -> None:
        del self.timer
        self.end()


@dataclass
class Say(Timed, Action):
    actor: str
    line: str

    def __post_init__(self) -> None:
        self.duration = len(self.line.split()) / 3.3

    def update(self) -> None:
        super().update()
        log.info(f"{self.actor}: {self.line}")


@dataclass
class Animate(Timed, Action):
    actor: str
    animation: Any

    def __post_init__(self) -> None:
        self.duration = 1.0

    def update(self) -> None:
        super().update()
        log.info(f"{self.actor} *{self.animation}*")


@dataclass
class Pause(Timed, Action):
    duration: float

    def update(self) -> None:
        super().update()
        log.info("...")


@dataclass
class NextState(Action):
    next_state: str

    def update(self) -> None:
        self.end(self.next_state)


Option = TypedDict("Option", {"value": str, "text": str, "if": str})


class OptionSelected(CustomEvent):
    pass


@dataclass
class Branch(Action):
    all_options: list[Option]

    def __post_init__(self) -> None:
        self.times_seen = Counter()

    @property
    def options(self) -> list[Option]:
        return list(filter(self.is_shown, self.all_options))

    def is_shown(self, option: Option) -> bool:
        return self.context.eval(
            option.get("if", "True"), _seen=self.times_seen[option["text"]]
        )

    @event_listener
    def select(self, event: OptionSelected) -> None:
        for option in event.options_shown:
            self.times_seen[option["text"]] += 1
        self.end(event.options_shown[event.selection]["value"])

    def update(self) -> None:
        for i, option in enumerate(self.options):
            log.info(f"{i}. {option['text']}")
