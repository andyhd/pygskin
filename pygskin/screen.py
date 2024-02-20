from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

import pygame

from pygskin import ecs
from pygskin.display import Display
from pygskin.pubsub import message
from pygskin.statemachine import StateMachine
from pygskin.utils import Decorator


class Screen(pygame.sprite.Sprite, ecs.Entity, ecs.Container):
    def __init__(self) -> None:
        pygame.sprite.Sprite.__init__(self, Display.sprites)
        ecs.Entity.__init__(self)

        self.rect = Display.rect

    @property
    def image(self) -> pygame.Surface:
        if not hasattr(self, "_image"):
            self._image = pygame.Surface(self.rect.size).convert_alpha()
        return self._image

    def load(self, state: dict) -> None:
        pass

    def unload(self) -> None:
        pass

    @message
    def exit(self, *args, **kwargs) -> None:
        self.unload()
        self.kill()
        ecs.Entity.instances.remove(self)

    def update(self, **kwargs) -> None:
        ecs.Container.update(self, **kwargs)

    @classmethod
    def transition(cls, fn: Callable) -> ScreenTransition:
        transition = ScreenTransition()
        transition.set_args(cls)
        transition.set_function(fn)
        return transition


class ScreenManager:
    def update(self) -> None:
        self.screen.update()

    def _initialise_statemachine(self) -> None:
        transition_table = {}

        def is_transition(attr):
            return isinstance(attr, ScreenTransition)

        for name, transition in inspect.getmembers_static(self, is_transition):
            transition_table.setdefault(transition.screen_class, []).append(
                getattr(self, name)
            )

        self._statemachine = StateMachine(transition_table)

    @property
    def screen(self) -> Screen:
        return self._screen

    @screen.setter
    def screen(self, screen: Screen) -> None:
        if not hasattr(self, "_screen"):
            self._initialise_statemachine()
        self._screen = screen
        self._statemachine.state = screen.__class__
        screen.load(self.state)
        screen.exit.subscribe(self.next_screen)

    @property
    def state(self) -> dict:
        if not hasattr(self, "_state"):
            self._state = {}
        return self._state

    @state.setter
    def state(self, value: dict) -> None:
        self._state = value

    def next_screen(self, *args) -> None:
        self.state["output"] = args
        self._statemachine.send(self.state)


class ScreenTransition(Decorator):
    def set_args(self, *args, **kwargs) -> None:
        super().set_args(*args, **kwargs)
        if args and issubclass(args[0], Screen):
            self.screen_class = args[0]

    def call_function(self, *args) -> Any:
        if next_screen := super().call_function():
            self.obj.screen = next_screen
            return next_screen.__class__


screen_transition = ScreenTransition
