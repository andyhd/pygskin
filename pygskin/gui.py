from __future__ import annotations

from contextlib import suppress
from typing import cast

import pygame
from pygame import Surface
from pygame import Vector2
from pygame.sprite import Sprite

from pygskin import ecs
from pygskin.display import Display
from pygskin.events import MouseButtonDown
from pygskin.events import MouseButtonUp
from pygskin.events import MouseMotion
from pygskin.events import event_listener
from pygskin.layout import Fill
from pygskin.layout import Layout
from pygskin.layout import LayoutItems
from pygskin.pubsub import message
from pygskin.text import Text
from pygskin.utils import Padding


class Widget(ecs.Entity, Sprite):
    def __init__(self, **kwargs) -> None:
        ecs.Entity.__init__(self)
        Sprite.__init__(self)

        self.style: dict = kwargs.pop("style", {})

        self.redraw = message()
        self.redraw.subscribe(self.clear_cached_image)

    @property
    def image(self):
        if not self._Sprite__image:
            rect = self.rect or self.preferred_rect
            self._Sprite__image = img = Surface(rect.size).convert_alpha()
            self.draw(img)
        return self._Sprite__image

    @image.setter
    def image(self, value) -> None:
        self._Sprite__image = value

    @property
    def rect(self):
        return self._Sprite__rect

    @rect.setter
    def rect(self, value) -> None:
        self._Sprite__rect = pygame.Rect(value)
        self.clear_cached_image()

    @property
    def preferred_rect(self) -> pygame.Rect | pygame.FRect:
        return pygame.Rect(0, 0, 100, 100)

    def clear_cached_image(self) -> None:
        self._Sprite__image = None

    def draw(self, surface: Surface) -> None:
        surface.fill(self.style.get("background") or "grey")


class Container(Widget):
    @property
    def layout(self) -> Layout:
        if not hasattr(self, "_layout"):
            self._layout: Layout = Fill()
        return self._layout

    @layout.setter
    def layout(self, value: Layout) -> None:
        self._layout = value

    @property
    def children(self) -> list[Sprite]:
        if not hasattr(self, "_children"):
            self._children: list[Sprite] = []
        return self._children

    def add_child(self, child: Sprite) -> None:
        self.children.append(child)
        if hasattr(child, "redraw"):
            child.redraw.subscribe(self.redraw)

    def remove_child(self, child: Sprite) -> None:
        if child in self.children:
            self.children.remove(child)
            if hasattr(child, "redraw"):
                child.redraw.subscribers.remove(self.redraw)

    def draw(self, surface: Surface) -> None:
        super().draw(surface)
        if self.rect:
            self.layout(self.rect, cast(LayoutItems, self.children))

            offset = Vector2(self.rect.topleft)

            surface.blits(
                (
                    child.image,
                    Vector2(child.rect.topleft) - offset,
                    ((0, 0), child.rect.size),
                )
                for child in self.children
                if child and child.rect
            )


class Root(Container):
    """
    GUI root container

    All other widgets are contained in this.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if not self.rect:
            self.rect = Display.rect


class Label(Widget):
    def __init__(self, text: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.text = text
        self._text = Text(self.text, **self.style)
        if self.rect is None:
            self.rect = self._text.rect

    def _invalidate_cached_text_image(self) -> None:
        with suppress(AttributeError):
            del self._text.image
            del self._text.rect

    def draw(self, surface: Surface) -> None:
        super().draw(surface)

        if self.rect:
            rect = pygame.Rect((0, 0), self.rect.size)

            align = self._text.align
            self._invalidate_cached_text_image()
            text_width = self._text.rect.width
            aligned = ((align * (rect.width - text_width)), 0)

            text_rect = self._text.rect.move(*aligned)
            text_rect.centery = rect.height // 2

            surface.fill(self.style.get("background") or (0, 0, 0, 0))
            surface.blit(self._text.image, text_rect)

    def set_text(self, text: str) -> str:
        self.text = text
        self._text.text = self.text
        self.redraw()
        return self.text


def lighten(color: pygame.Color, quotient: float) -> pygame.Color:
    return color.lerp("white", quotient)


def darken(color: pygame.Color, quotient: float) -> pygame.Color:
    return color.lerp("black", quotient)


class Button(Label):
    def __init__(
        self,
        text: str,
        pressed: bool = False,
        hover: bool = False,
        **kwargs,
    ) -> None:
        if style := kwargs.get("style"):
            bg = pygame.Color(style.get("background") or "grey")
            style["background"] = pygame.Color(0, 0, 0, 0)
        super().__init__(text, **kwargs)
        self.pressed = pressed
        self.hover = hover
        style.setdefault("align", "CENTER")
        self.colors = {
            "bg": bg,
            "hover_bg": style.get("hover_background", lighten(bg, 0.2)),
            "shadow": style.get("shadow_color", darken(bg, 0.3)),
            "border": style.get("border_color", darken(bg, 0.6)),
        }
        self.click = message()

    def draw(self, surface: Surface) -> None:
        super().draw(surface)

        if not self.rect:
            return

        color = self.colors["bg"]
        hover = self.colors["hover_bg"]
        shadow = self.colors["shadow"]
        border = self.colors["border"]
        rect = pygame.Rect((0, 0), self.rect.size)

        with suppress(AttributeError):
            del self._text.image
            del self._text.rect

        # align text in button
        align = self._text.align
        text_width = self._text.rect.width
        aligned = ((align * (rect.width - text_width)), 0)

        text_rect = self._text.rect.move(*aligned)
        text_rect.centery = rect.height // 2

        surface.fill(shadow)
        if self.pressed:
            surface.blit(self._text.image, text_rect.move(0, 4))
        else:
            surface.set_clip(rect.move(0, -5))
            surface.fill(hover if self.hover else color)
            surface.blit(self._text.image, text_rect)
            surface.set_clip(None)

        pygame.draw.rect(surface, border, rect, 1)

    @event_listener
    def mouse_down(self, event: MouseButtonDown) -> None:
        if self.rect.collidepoint(event.pos):
            self.pressed = True
            self.redraw()

    @event_listener
    def mouse_up(self, event: MouseButtonUp) -> None:
        if self.pressed and self.rect.collidepoint(event.pos):
            self.pressed = False
            self.redraw()
            self.click()

    @event_listener
    def mouse_move(self, event: MouseMotion) -> None:
        redraw = False

        if self.rect.collidepoint(event.pos):
            if not self.hover:
                self.hover = True
                redraw = True
        else:
            if self.hover:
                self.hover = False
                redraw = True

            if self.pressed:
                self.pressed = False
                redraw = True

        if redraw:
            self.redraw()


class Checkbox(Label):
    def __post_init__(
        self,
        text: str,
        checked: bool = False,
        radio: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(text, **kwargs)
        self.checked = checked
        self.radio = radio
        self._text = Text(self.text, **self.style)
        line_height = self._text.font.get_linesize()
        descent = self._text.font.get_descent()
        margin = self.style.get("margin", Padding(3))
        spacing = self.style.get("spacing", 3)
        self.button_rect = button_rect = pygame.Rect(
            (margin.left, margin.top),
            Vector2(line_height + descent),
        )
        self.text_offset = text_offset = Vector2(
            button_rect.right + spacing,
            margin.top,
        )
        self.rect = pygame.Rect(
            0,
            0,
            text_offset.x + self._text.rect.width + margin.right,
            text_offset.y + self._text.rect.height + margin.bottom,
        )
        self.change = message()

    def draw(self, surface: Surface) -> None:
        super().draw(surface)

        color = pygame.Color(self.style.get("background") or "grey")
        shadow = color.lerp(pygame.Color("black"), 0.2)

        self._text.background = color
        with suppress(AttributeError):
            del self._text.image
            del self._text.rect

        surface.fill(color)
        if self.radio:
            pygame.draw.circle(surface, shadow, (15, 15), 15, width=1)
            if self.checked:
                pygame.draw.circle(surface, shadow, (15, 15), 10)
        else:
            self.draw_checkbox(surface, pygame.Rect(self.button_rect))

        self._text.rect.topleft = self.text_offset
        surface.blit(self._text.image, self._text.rect)

    def draw_checkbox(self, surface: Surface, rect: pygame.Rect) -> None:
        color = pygame.Color(self.style.get("background") or "grey")
        shadow = color.lerp(pygame.Color("black"), 0.5)
        hilite = color.lerp(pygame.Color("white"), 0.5)
        fill = color.lerp(pygame.Color("white"), 0.75)

        pygame.draw.rect(surface, fill, rect)

        for _ in range(2):
            pygame.draw.line(surface, shadow, rect.topleft, rect.topright)
            pygame.draw.line(surface, shadow, rect.topleft, rect.bottomleft)
            pygame.draw.line(surface, hilite, rect.bottomleft, rect.bottomright)
            pygame.draw.line(surface, hilite, rect.bottomright, rect.topright)
            rect.inflate_ip(-1, -1)

        if self.checked:
            rect.inflate_ip(-6, -6)
            for offset in range(-1, 2):
                nw = Vector2(rect.topleft) + (offset, offset * -1)
                se = Vector2(rect.bottomright) + (offset, offset * -1)
                ne = Vector2(rect.topright) + Vector2(offset)
                sw = Vector2(rect.bottomleft) + Vector2(offset)

                pygame.draw.line(surface, shadow, nw, se, width=2)
                pygame.draw.line(surface, shadow, ne, sw, width=2)

    @event_listener
    def mouse_down(self, event: MouseButtonDown) -> None:
        if self.rect.collidepoint(event.pos):
            self.pressed = True

    @event_listener
    def mouse_up(self, event: MouseButtonUp) -> None:
        if self.pressed and self.rect.collidepoint(event.pos):
            self.pressed = False
            self.checked = not self.checked
            self.redraw()
            self.change(self)
