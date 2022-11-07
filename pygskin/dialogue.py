from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame
from ruamel.yaml import YAML

from pygskin import pubsub
from pygskin.state_machine import StateMachine
from pygskin.state_machine import Transition
from pygskin.text import Text


class Condition:
    def __init__(self, conditions: list[str] | None, context: dict[str, Any]) -> None:
        self.conditions = conditions
        self.context = context

    def __call__(self, *_) -> bool:
        if self.conditions is None:
            return True
        return all(
            eval(expr, {"_seen": False}, self.context) for expr in self.conditions
        )

    def __repr__(self) -> str:
        conditions = " and ".join(self.conditions) if self.conditions else None
        return f"<Condition {conditions}>"


class Dialogue(StateMachine[str | None, str]):
    def __init__(
        self,
        parts: dict[str, list[Action]],
        context: dict[str, Any],
    ) -> None:
        self.context = context
        self.parts = parts
        self.action_index = 0

        transition_table = {}

        for name, actions in self.parts.items():
            for action in actions:
                action.context = self.context
                action.end.subscribe(self.next_action)
                transition_table.setdefault(name, []).extend(action.transitions)

        super().__init__(transition_table, initial_state="start")

    @staticmethod
    def load(filename: str) -> Dialogue:
        yaml = YAML(typ="safe")
        with open(filename, "r") as f:
            data = yaml.load(f.read())

        del data["location"]
        del data["characters"]

        context = data.pop("init_vars", {})

        return Dialogue(
            {
                name: [Action.build(_) for _ in actions]
                for name, actions in data.items()
            },
            context,
        )

    @property
    def actions(self) -> list[Action]:
        return self.parts[self.state]

    @property
    def action(self) -> Action:
        return self.actions[self.action_index]

    def next_action(self, input: str | None = None) -> None:
        while input is None and self.action_index + 1 <= len(self.actions):
            self.action_index += 1
            if Condition(self.action.conditions, self.context)():
                return

        self.action_index = 0
        self.next_state(input)

    def update(self, dt: int) -> None:
        self.action.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self.action.draw(surface)

    def select_prompt(self, index: int) -> None:
        if hasattr(self.action, "select") and callable(self.action.select):
            self.action.select(index)


class Action:
    def __init__(self, params: Any, conditions: list[str] | None = None) -> None:
        self.params = params
        self.conditions = conditions
        self.end = pubsub.Message()
        self.end.subscribe(self.setup)
        self.context = {}
        self.setup()

    def setup(self, *_) -> None:
        pass

    @staticmethod
    def build(data: dict[str, Any]) -> Action:
        conditions = data.pop("when", None)
        name, params = data.popitem()
        class_name = "".join(word.capitalize() for word in name.split("_"))

        try:
            ActionClass = {_.__name__: _ for _ in Action.__subclasses__()}[class_name]
        except KeyError:
            try:
                ActionClass = Animate
                params = {"actor": name, "animation": params["animation"]}
            except TypeError:
                ActionClass = Say
                params = {"actor": name, "line": str(params)}

        return ActionClass(params, conditions=conditions)

    @property
    def transitions(self) -> list[Transition]:
        return []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.params}>"

    def update(self, _) -> None:
        pass

    def draw(self, _) -> None:
        pass


class SetVars(Action):
    def update(self, _) -> None:
        for var_name, expr in self.params.items():
            self.context[var_name] = eval(str(expr), {}, self.context)

        self.end()


class Say(Action):
    def setup(self, *_) -> None:
        self.text = Text(f"{self.params['actor']}: {self.params['line']}")
        self.start_ttl = int(len(self.params["line"].split()) / 3.3 * 1000)
        self.ttl = self.start_ttl

    def update(self, dt: int) -> None:
        self.ttl -= dt
        if self.ttl <= 0:
            self.end()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.text.image, self.text.rect)


class Animate(Action):
    def setup(self, *_) -> None:
        self.text = Text(f"{self.params['actor']}: *{self.params['animation']}*")
        self.ttl = 1000

    def update(self, dt: int) -> None:
        self.ttl -= dt
        if self.ttl <= 0:
            self.end()


class Pause(Action):
    def setup(self, *_) -> None:
        self.ttl = int(self.params * 1000)

    def update(self, dt: int) -> None:
        self.ttl -= dt
        if self.ttl <= 0:
            self.end()


class NextState(Action):
    @property
    def transitions(self) -> list[tuple]:
        return [(self.params, self.params, Condition(self.conditions, self.context))]

    def update(self, _) -> None:
        self.end(self.params)


class Prompt(Action):
    @dataclass
    class Option:
        to_state: str
        text: str
        value: int
        conditions: list[str] | None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._seen = set()
        self.all_options = []
        for value, prompt in enumerate(self.params):
            conditions = prompt.pop("when", None)
            to_state, text = prompt.popitem()
            self.all_options.append(Prompt.Option(to_state, text, value, conditions))

    def setup(self, *_) -> None:
        self.selection = None

    @property
    def transitions(self) -> list[tuple]:
        return [
            (
                option.to_state,
                option.to_state,
                Condition(option.conditions, self.context),
            )
            for option in self.all_options
        ]

    @property
    def options(self) -> list[Prompt.Option]:
        def is_shown(option):
            context = {"_seen": option.text in self._seen, **self.context}
            return Condition(option.conditions, context)()

        return list(filter(is_shown, self.all_options))

    def update(self, _) -> None:
        if self.selection is None:
            return
        self.end(self.all_options[self.selection].to_state)

    def draw(self, surface: pygame.Surface) -> None:
        text = Text(
            "\n".join(f"{option.value}. {option.text}" for option in self.options)
        )
        surface.blit(text.image, text.rect)

    def select(self, index: int) -> None:
        self.selection = index


def test_dialogue():

    from pygame import K_0, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_SPACE
    from pygskin.events import KeyDown
    from pygskin.input import Input
    from pygskin.window import Window

    pygame.font.init()

    dialogue = Dialogue.load("tests/test_dialogue.yaml")

    with Window((800, 600), background="black") as window:

        window.event_map = {
            KeyDown(K_0): Input(dialogue.select_prompt, 0),
            KeyDown(K_1): Input(dialogue.select_prompt, 1),
            KeyDown(K_2): Input(dialogue.select_prompt, 2),
            KeyDown(K_3): Input(dialogue.select_prompt, 3),
            KeyDown(K_4): Input(dialogue.select_prompt, 4),
            KeyDown(K_5): Input(dialogue.select_prompt, 5),
            KeyDown(K_6): Input(dialogue.select_prompt, 6),
            KeyDown(K_7): Input(dialogue.select_prompt, 7),
            KeyDown(K_8): Input(dialogue.select_prompt, 8),
            KeyDown(K_SPACE): Input(dialogue.next_state, None),
        }

        while window.running:
            dt = window.tick()

            dialogue.update(dt)
            dialogue.draw(window.surface)
