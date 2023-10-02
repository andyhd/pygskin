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
        self.image = pygame.Surface(self.rect.size).convert_alpha()

    def load(self, state: dict) -> None:
        pass

    def unload(self) -> None:
        pass

    @message
    def exit(self, *args) -> None:
        self.unload()
        self.kill()
        ecs.Entity.instances.remove(self)

    def update(self, **kwargs) -> None:
        ecs.Container.update(self, **kwargs)


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
    # TODO take from-state as decorator argument
    #      eg: @screen_transition(MainMenu)
    #      or make inner class of Screen class, eg:
    #      @MainMenu.Transition
    def set_function(self, fn: Callable) -> None:
        super().set_function(fn)

        sig = inspect.signature(fn, eval_str=True)
        for i, (name, param) in enumerate(sig.parameters.items()):
            if i == 0 and name == "self":
                continue
            if issubclass(param.annotation, Screen):
                self.screen_class = param.annotation
                break
        else:
            raise ValueError("ScreenTransition must specify a Screen as first argument")

    def call_function(self, *args) -> Any:
        if next_screen := super().call_function(self.obj.screen):
            self.obj.screen = next_screen
            return next_screen.__class__


screen_transition = ScreenTransition
