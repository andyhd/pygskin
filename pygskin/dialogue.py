"""Dialogue system for PygSkin."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import NamedTuple

from pygskin.statemachine import StateMachine
from pygskin.statemachine import TransitionTable

Context = dict[str, Any]


@dataclass
class Action:
    """Base class for all actions."""

    condition: str | None = field(default=None, kw_only=True, repr=False)

    def execute(self, context: Context) -> None:
        pass


@dataclass
class UpdateContext(Action):
    """Update the context with the results of evaluating the assignments.

    >>> context = {"x": 2}
    >>> UpdateContext({"x": "x + 1"}).execute(context)
    >>> context["x"]
    3
    """

    assignments: dict[str, Any]

    def execute(self, context: Context) -> None:
        context.update(
            (var, eval(str(expr), context)) for var, expr in self.assignments.items()
        )


Actor = str
WORDS_PER_SEC = 3.3


@dataclass
class Line(Action):
    """A line of dialogue spoken by an actor."""

    actor: Actor
    text: str
    duration: float = field(default=1.0, repr=False)

    def __post_init__(self) -> None:
        self.duration = max(len(self.text.split()) / WORDS_PER_SEC, 1.0)


@dataclass
class StageDirection(Action):
    """A stage direction for actors to follow."""

    actors: list[Actor]
    direction: str


@dataclass
class Pause(Action):
    """Pause the dialogue for a specified duration."""

    duration: float = 1.0


@dataclass
class ChangeScene(Action):
    """Change the scene to the specified scene."""

    scene: str

    def execute(self, context: Context) -> None:
        context["change_scene"] = self.scene


class Option(NamedTuple):
    value: str
    text: str
    condition: str = "True"

    def __repr__(self) -> str:
        return f"Option(value={self.value!r}, text={self.text!r})"


@dataclass
class Select(Action):
    """Select an option.

    >>> context = {"asked": 1}
    >>> select = Select([
    ...     Option(value="say_no", text="Are we there yet?"),
    ...     Option(value="curse", text="How about now?", condition="asked >= 2"),
    ... ])
    >>> select.options(context)
    [Option(value='say_no', text='Are we there yet?')]
    >>> context["asked"] += 1
    >>> select.options(context)  # doctest: +NORMALIZE_WHITESPACE
    [Option(value='say_no', text='Are we there yet?'),
     Option(value='curse', text='How about now?')]
    >>> select.select(
    ...     Option(value="curse", text="How about now?", condition="asked >= 2"),
    ...     context,
    ... )
    >>> context["change_scene"]
    'curse'
    """

    all_options: list[Option]

    def __post_init__(self) -> None:
        self.times_seen: Counter[Option] = Counter()

    def options(self, context: Context) -> list[Option]:
        """Return the options that are shown."""
        shown = [
            option
            for option in self.all_options
            if eval(option.condition, context, {"_seen": self.times_seen[option]})
        ]
        self.times_seen.update(shown)
        return shown

    def select(self, option: Option, context: Context) -> None:
        """Select an option."""
        context.update({"change_scene": option.value})


@dataclass
class ActionTransition:
    """A transition from one Action to another."""

    next_state: int | None
    condition: str | None = None

    def __call__(self, context: Context) -> int | None:
        if self.condition is None or eval(self.condition, context):
            return self.next_state
        return None


class Scene(StateMachine[int]):
    """A scene in a dialogue.

    >>> context = {"bob_is_lazy": True}
    >>> scene = Scene([
    ...     Line(actor="Alice", text="Good work, everyone!"),
    ...     Line(actor="Bob", text="Thanks, Alice!"),
    ...     Line(actor="Alice", text="You too, Bob.", condition="not bob_is_lazy"),
    ...     Line(actor="Alice", text="Not you, Bob.", condition="bob_is_lazy"),
    ... ])
    >>> scene.action
    Line(actor='Alice', text='Good work, everyone!')
    >>> scene.send(context)
    1
    >>> scene.action
    Line(actor='Bob', text='Thanks, Alice!')
    >>> scene.send(context)
    3
    >>> scene.action
    Line(actor='Alice', text='Not you, Bob.')
    """

    def __init__(self, actions: list[Action]) -> None:
        self.actions = actions
        transitions = TransitionTable[int]()

        branch_point: int | None = None
        else_: ActionTransition = ActionTransition(None)

        for from_state, (next_state, action) in enumerate(enumerate(actions[1:], 1)):
            to_next_state = ActionTransition(next_state, action.condition)

            if action.condition:
                if branch_point is None:
                    branch_point = from_state

                transitions.setdefault(branch_point, []).append(to_next_state)

                if from_state != branch_point:
                    transitions.setdefault(from_state, []).append(else_)

            else:
                if branch_point is not None:
                    else_.next_state = next_state
                    else_ = ActionTransition(None)
                    branch_point = None

                transitions.setdefault(from_state, []).append(to_next_state)

        super().__init__(transitions)

    @property
    def action(self) -> Action:
        """Return the current action."""
        return self.actions[self.state or 0]


def scene_transition(context: Context) -> str | None:
    """A transition from one scene to another."""
    return context.pop("change_scene", None)


class Dialogue(StateMachine[str]):
    """A dialogue consisting of multiple scenes.

    >>> context = {}
    >>> dialogue = Dialogue({
    ...     "scene1": Scene([Line("Alice", "Hello, world!"), ChangeScene("scene2")]),
    ...     "scene2": Scene([Line("Bob", "Goodbye, world!"), ChangeScene("scene1")]),
    ... })
    >>> dialogue.transition_table  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    {'scene1': [<function scene_transition at ...>],
     'scene2': [<function scene_transition at ...>]}
    >>> dialogue.scene.action
    Line(actor='Alice', text='Hello, world!')
    >>> dialogue.scene.send(context)
    1
    >>> dialogue.scene.action
    ChangeScene(scene='scene2')
    >>> dialogue.scene.action.execute(context)
    >>> dialogue.send(context)
    'scene2'
    >>> dialogue.scene.action
    Line(actor='Bob', text='Goodbye, world!')
    """

    def __init__(
        self, scenes: dict[str, Scene], context: Context | None = None
    ) -> None:
        self.scenes = scenes
        self.context = context or {}
        super().__init__(
            TransitionTable[str](**{scene: [scene_transition] for scene in scenes}),
        )

    @property
    def scene(self) -> Scene:
        """Return the current scene."""
        if self.state is None:
            return list(self.scenes.values())[0]
        return self.scenes[self.state]


def load_dialogue(data: dict) -> Dialogue:
    """Load a dialogue from a dict.

    >>> json_data = {
    ...     "context": {"bob_is_lazy": True},
    ...     "scene1": [
    ...         {"Alice": "Good work, everyone!"},
    ...         {"Bob": "Thanks, Alice!"},
    ...         {"Alice": "You too, Bob.", "if": "not bob_is_lazy"},
    ...         {"Alice": "Not you, Bob.", "if": "bob_is_lazy"},
    ...         {"next_state": "scene2"},
    ...     ],
    ...     "scene2": [
    ...         {"Alice": "Goodbye, world!"},
    ...         {"Bob": "Hello, world!"},
    ...     ],
    ... }
    >>> dialogue = load_dialogue(json_data)
    >>> dialogue.scene.action
    Line(actor='Alice', text='Good work, everyone!')
    >>> dialogue.scene.send(dialogue.context)
    1
    >>> dialogue.scene.action
    Line(actor='Bob', text='Thanks, Alice!')
    >>> dialogue.scene.send(dialogue.context)
    3
    >>> dialogue.scene.action
    Line(actor='Alice', text='Not you, Bob.')
    """
    context: Context = data.pop("context", {})
    scenes = {name: load_scene(scene_data) for name, scene_data in data.items()}
    return Dialogue(scenes, context)


def load_scene(scene_data: list[dict]) -> Scene:
    """Load a scene from a list of action data.

    >>> context = {"bob_is_lazy": True}
    >>> scene_data = [
    ...     {"Alice": "Good work, everyone!"},
    ...     {"Bob": "Thanks, Alice!"},
    ...     {"Alice": "You too, Bob.", "if": "not bob_is_lazy"},
    ...     {"Alice": "Not you, Bob.", "if": "bob_is_lazy"},
    ... ]
    >>> scene = load_scene(scene_data)
    >>> scene.action
    Line(actor='Alice', text='Good work, everyone!')
    >>> scene.send(context)
    1
    >>> scene.action
    Line(actor='Bob', text='Thanks, Alice!')
    >>> scene.send(context)
    3
    >>> scene.action
    Line(actor='Alice', text='Not you, Bob.')
    """
    return Scene([load_action(action_data) for action_data in scene_data])


def load_action(action_data: dict) -> Action:
    """Load an action from a dict.

    >>> load_action({"Alice": "Good work, everyone!"})
    Line(actor='Alice', text='Good work, everyone!')
    >>> load_action({"Alice": "Not you, Bob.", "if": "bob_is_lazy"})
    Line(actor='Alice', text='Not you, Bob.')
    >>> load_action({"next_state": "scene2"})
    ChangeScene(scene='scene2')
    >>> load_action({"branch": [
    ...     {"value": "say_no", "text": "Are we there yet?"},
    ...     {"value": "curse", "text": "How about now?"},
    ... ]})  # doctest: +NORMALIZE_WHITESPACE
    Select(all_options=[Option(value='say_no', text='Are we there yet?'),
                        Option(value='curse', text='How about now?')])
    >>> load_action({"pause": 1.0})
    Pause(duration=1.0)
    >>> load_action({"Alice": {"animation": "wave"}})
    StageDirection(actors=['Alice'], direction='wave')
    >>> load_action({"update_context": {"x": "x + 1"}})
    UpdateContext(assignments={'x': 'x + 1'})
    """
    condition = action_data.pop("if", None)
    match list(action_data.items())[0]:
        case "update_context", dict(assignments):
            return UpdateContext(assignments, condition=condition)
        case "next_state", str(scene):
            return ChangeScene(scene, condition=condition)
        case "branch", list(options):
            return Select([load_option(option) for option in options])
        case "pause", float(duration):
            return Pause(duration, condition=condition)
        case str(actor), {"animation": str(direction)}:
            return StageDirection([actor], direction, condition=condition)
        case str(actor), str(text):
            return Line(actor, text, condition=condition)
        case _:
            raise ValueError(f"Unknown action: {action_data}")


def load_option(option_data: dict) -> Option:
    """Load an option from a dict.

    >>> load_option({"value": "say_no", "text": "Are we there yet?"})
    Option(value='say_no', text='Are we there yet?')
    >>> load_option({"value": "curse", "text": "How about now?", "if": "asked >= 2"})
    Option(value='curse', text='How about now?')
    """
    condition = option_data.pop("if", None)
    return Option(**option_data, condition=condition)
