import inspect
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from enum import IntFlag
from typing import Any

import pygame
import pygame.locals as pg
from pygame import Event
from pygame import Font
from pygame import FRect
from pygame import Rect
from pygame import Surface

from pygskin.rect import add_padding
from pygskin.rect import align_rect
from pygskin.rect import get_rect_attrs

Flag = IntFlag(
    "Flag",
    "CLICKABLE EDITABLE FOCUSABLE SCROLLABLE HAS_BORDER HAS_BACKGROUND HAS_SHADOW",
)
PseudoClass = Enum("PseudoClass", "HOVER ACTIVE FOCUS")


def get_widget_id() -> int:
    """Generate a unique widget ID based on the position in the source code."""
    frame_info = inspect.stack()[2]
    return hash((frame_info.filename, tuple(frame_info.positions)))


@dataclass
class Widget:
    value: Any
    type: str
    flags: int = 0
    id: str | None = None
    classes: list[str] = field(default_factory=list)
    rect: Rect = field(default_factory=lambda: Rect(0, 0, 0, 0))
    pseudo_classes: set[PseudoClass] = field(default_factory=set)


def draw_widget(widget: Widget, *, surface: Surface, **style) -> None:
    if widget.rect:
        if PseudoClass.FOCUS in widget.pseudo_classes:
            draw_focus(surface, widget, **style)
        if widget.flags & Flag.HAS_BACKGROUND:
            draw_background(surface, widget, **style)
        if widget.type == "radio":
            draw_radio_button(surface, widget, **style)
        if widget.flags & Flag.HAS_BORDER:
            draw_border(surface, widget, **style)
        if text := get_widget_text(widget):
            draw_text(surface, text, widget, **style)


def draw_focus(surface: Surface, widget: Widget, **style) -> None:
    pygame.draw.rect(
        surface,
        style.get("focus_boder_color", "red"),
        widget.rect.inflate(4, 4),
        width=style.get("focus_border_width", 4),
        border_radius=style.get("focus_border_radius", 0),
    )


def draw_background(surface: Surface, widget: Widget, **style) -> None:
    color = style.get(
        "background_color",
        "white" if PseudoClass.ACTIVE in widget.pseudo_classes else "black",
    )
    pygame.draw.rect(
        surface,
        color,
        widget.rect,
        width=0,
        border_radius=style.get("border_radius", 0),
    )


def draw_border(surface: Surface, widget: Widget, **style) -> None:
    pygame.draw.rect(
        surface,
        style.get("border_color", "white"),
        widget.rect,
        width=style.get("border_width", 1),
        border_radius=style.get("border_radius", 0),
    )


def get_widget_text(widget: Widget) -> str | None:
    """Extract text from a widget's value."""
    match widget.value:
        case str(text):
            return text
        case list(text_list):
            return "".join(text_list)
        case (str(text), _):
            return text
        case _:
            return None


def draw_text(surface: Surface, text: str, widget: Widget, **style) -> None:
    font = style.get("font", Font(None, style.get("font_size", 30)))
    color = style.get("color", "white")
    text_img = font.render(text, True, color)
    text_rect = text_img.get_rect(center=widget.rect.center)
    align_rect(
        text_rect,
        widget.rect,
        style.get("align", "center"),
        style.get("valign", "middle"),
    )
    _, text_rect = add_padding(text_rect, style.get("padding", 0))
    surface.blit(text_img, text_rect)


def draw_radio_button(surface: Surface, widget: Widget, **style) -> None:
    box = widget.rect.move_to(
        width=widget.rect.height,
        right=widget.rect.x - 5,
        y=widget.rect.y - widget.rect.height * 0.1,
    )
    pygame.draw.rect(surface, style.get("border_color", "white"), box, 1)
    if style.get("checked"):
        check = FRect(box).scale_by(0.5)
        pygame.draw.rect(surface, style.get("border_color", "white"), check)


def label(text: str | list[str], **kwargs) -> Widget:
    return Widget(text, type="label", **kwargs)


def button(text: str | list[str], **kwargs) -> Widget:
    return Widget(
        text,
        flags=Flag.CLICKABLE | Flag.FOCUSABLE | Flag.HAS_BORDER | Flag.HAS_BACKGROUND,
        type="button",
        **kwargs,
    )


def textfield(value: list[str], **kwargs) -> Widget:
    return Widget(
        value,
        flags=Flag.EDITABLE | Flag.FOCUSABLE | Flag.HAS_BORDER | Flag.HAS_BACKGROUND,
        type="textfield",
        **kwargs,
    )


def radio(value: str | list[str], **kwargs) -> Widget:
    return Widget(
        value,
        flags=Flag.CLICKABLE | Flag.FOCUSABLE | Flag.HAS_BACKGROUND,
        type="radio",
        **kwargs,
    )


class IMGUI:
    def __init__(self, get_styles: Callable | None = None):
        self.active: int | None = None
        self.hot: int | None = None
        self.focus: int | None = None
        self.tabindex_prev: int | None = None
        self.events: list[Event] = []
        self.get_styles = get_styles

    @contextmanager
    def __call__(self, surface: Surface, events: list[Event]) -> Iterator[Callable]:
        self.surface = surface
        self.events = events

        yield self.render

        self.hot = None
        if not pygame.mouse.get_pressed()[0]:
            self.active = None
        elif self.active is None:
            self.active = -1

    def render(self, widget: Widget, **style) -> Widget:
        widget_id = get_widget_id()

        if callable(self.get_styles):
            style = self.get_styles(widget) | style

        rect = widget.rect
        if not rect:
            rect = Rect(0, 0, 0, 0)
            if text := get_widget_text(widget):
                font = style.setdefault("font", Font(None, style.get("font_size", 30)))
                rect.size = font.size(text)
            if padding := style.get("padding"):
                rect, _ = add_padding(rect, padding)
        if rect_kwargs := get_rect_attrs(style):
            rect = widget.rect = rect.move_to(**rect_kwargs)

        triggered = False

        if rect.collidepoint(pygame.mouse.get_pos()):
            self.hot = widget_id
            widget.pseudo_classes.add(PseudoClass.HOVER)

        mousedown_events = [
            e for e in self.events if e.type == pg.MOUSEBUTTONDOWN and e.button == 1
        ]
        if self.hot == widget_id and mousedown_events:
            self.active = widget_id
            widget.pseudo_classes.add(PseudoClass.ACTIVE)
            if widget.flags & Flag.CLICKABLE:
                triggered = True
                for e in mousedown_events:
                    # prevent event being processed by other widgets
                    e.button = 0

        if widget.flags & Flag.FOCUSABLE and self.focus is None:
            self.focus = widget_id

        if self.focus == widget_id:
            widget.pseudo_classes.add(PseudoClass.FOCUS)

            for event in self.events:
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_TAB:
                        self.focus = (
                            self.tabindex_prev if event.mod & pg.KMOD_SHIFT else None
                        )
                        # prevent event being processed by other widgets
                        event.key = 0

                    if widget.flags & Flag.EDITABLE:
                        if event.key == pg.K_BACKSPACE:
                            widget.value[:] = widget.value[:-1]
                            triggered = True

                        if 32 <= event.key < 127 and len(widget.value) < 30:
                            widget.value.append(event.unicode)
                            triggered = True

        draw_widget(widget, surface=self.surface, **style)

        if widget.flags & Flag.FOCUSABLE:
            self.tabindex_prev = widget_id

        return triggered


__all__ = [
    "IMGUI",
    "button",
    "label",
    "radio",
    "textfield",
]
