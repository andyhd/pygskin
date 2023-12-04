import pygame

from pygskin import ecs
from pygskin.assets import Assets
from pygskin.dialogue import Dialogue
from pygskin.dialogue import OptionSelected
from pygskin.display import Display
from pygskin.events import Event
from pygskin.events import KeyDown
from pygskin.events import MouseButtonDown
from pygskin.events import MouseMotion
from pygskin.events import Quit
from pygskin.events import event_listener
from pygskin.text import Text
from pygskin.window import Window

assets = Assets()


class Game(Window):
    def __init__(self):
        super().__init__(title="Dialogue")

        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        pygame.mouse.set_visible(True)

        self.dialogue = Dialogue(data=assets.ray_first_meeting)
        self.dialogue.action_changed.subscribe(self.init_action)
        self.dialogue.state_changed.subscribe(self.init_action)

        self.sprites = pygame.sprite.Group()
        self._buttons = {}

    @event_listener
    def quit(self, _: KeyDown.ESCAPE | Quit) -> None:
        self.running = False

    @event_listener
    def click(self, event: MouseButtonDown) -> None:
        if event.button == 1:
            for button_rect, (click_handler, args) in self._buttons.items():
                if pygame.Rect(*button_rect).collidepoint(event.pos):
                    click_handler(*args)
                    event.cancel()
                    break
            else:
                self.dialogue.scene.action.end()

    def init_action(self) -> None:
        for sprite in self.sprites:
            sprite.kill()
        self._buttons = {}
        action = self.dialogue.scene.action

        text_conf = {
            "wrap_width": Display.rect.width - 40,
            "padding": [0, 20],
        }

        if text := str(action):
            text_spr = Text(text, top=20, **text_conf)
            text_spr.add(self.sprites, Display.sprites)

        if options := getattr(action, "options", None):
            top = 20
            for i, option in enumerate(options):
                opt_spr = Option(
                    f"{i + 1}. {option['text']}",
                    hover={"color": pygame.Color("magenta")},
                    top=top,
                    **text_conf,
                )
                top += opt_spr.rect.height
                opt_spr.add(self.sprites, Display.sprites)
                self._buttons[tuple(opt_spr.rect)] = (
                    action.select,
                    (OptionSelected(options_shown=options, selection=i),),
                )

    def update(self) -> None:
        super().update()
        self.dialogue.update()


class MouseEnter(Event):
    pass


class MouseExit(Event):
    pass


class HandlesMouseOver:
    @property
    def under_mouse_cursor(self) -> bool:
        if not hasattr(self, "_under_mouse_cursor"):
            self._under_mouse_cursor = False
        return self._under_mouse_cursor

    @event_listener
    def mouseover(self, event: MouseMotion) -> None:
        mouse_in_rect = self.rect.collidepoint(event.pos)
        if mouse_in_rect and not self.under_mouse_cursor:
            self._under_mouse_cursor = True
            MouseEnter(target=self, pos=event.pos).post()
        elif not mouse_in_rect and self.under_mouse_cursor:
            self._under_mouse_cursor = False
            MouseExit(target=self, pos=event.pos).post()


class Option(ecs.Entity, HandlesMouseOver, Text):
    def __init__(self, *args, **kwargs) -> None:
        ecs.Entity.__init__(self)
        self.hover_style = kwargs.pop("hover", {})
        Text.__init__(self, *args, **kwargs)
        self.revert_style = {
            k: self.__dict__[k] for k in self.__dict__.keys() & self.hover_style.keys()
        }

    @event_listener
    def mouse_enter(self, event: MouseEnter) -> None:
        if event.target is self:
            del self.image
            self.__dict__.update(self.hover_style)

    @event_listener
    def mouse_exit(self, event: MouseExit) -> None:
        if event.target is self:
            del self.image
            self.__dict__.update(self.revert_style)


if __name__ == "__main__":
    Game().run()
