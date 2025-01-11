import contextlib
import inspect
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

import pygame
import pygame.locals as pg
from pygame.event import Event

from pygskin.rect import add_padding
from pygskin.rect import get_rect_attrs

CLICKABLE = 1
EDITABLE = 2
FOCUSABLE = 4
SCROLLABLE = 8
HAS_BORDER = 16
HAS_BACKGROUND = 32
HAS_SHADOW = 64


Align = Enum("Align", "left center right")
VAlign = Enum("VAlign", "top middle bottom")


@dataclass
class Widget:
    value: Any = None
    flags: int = 0
    rect: pygame.Rect | None = None
    triggered: bool = False
    type: str | None = None
    id: str | None = None
    classes: list[str] = field(default_factory=list)
    pseudo_classes: set[str] = field(default_factory=set)

    def draw(self, surface: pygame.Surface, **style) -> None:
        if "focus" in self.pseudo_classes:
            draw_widget_focus(surface, self, **style)
        draw_widget_background(surface, self, **style)
        draw_widget_border(surface, self, **style)
        draw_widget_text(surface, self, **style)


def label(text: str | list[str], **kwargs) -> Widget:
    return Widget(text, type="label", **kwargs)


def button(text: str | list[str], **kwargs) -> Widget:
    return Widget(
        text,
        CLICKABLE | FOCUSABLE | HAS_BORDER | HAS_BACKGROUND,
        type="button",
        **kwargs,
    )


def textfield(text: list[str], **kwargs) -> Widget:
    return Widget(
        text,
        EDITABLE | FOCUSABLE | HAS_BORDER | HAS_BACKGROUND,
        type="textfield",
        **kwargs,
    )


@dataclass
class radio(Widget):  # noqa
    flags: int = CLICKABLE | FOCUSABLE | HAS_BACKGROUND

    def draw(
        self,
        surface: pygame.Surface,
        has_focus: bool = False,
        checked: bool = False,
        **style,
    ) -> None:
        if has_focus:
            draw_widget_focus(surface, self, **style)
        draw_widget_background(surface, self, **style)
        if self.rect is not None:
            box = self.rect.move_to(
                width=self.rect.height,
                right=self.rect.x - 5,
                y=self.rect.y - self.rect.height * 0.1,
            )
            pygame.draw.rect(surface, style.get("border_color", "white"), box, 1)
            if checked:
                check = pygame.FRect(box).scale_by(0.5)
                pygame.draw.rect(surface, style.get("border_color", "white"), check)
        draw_widget_text(surface, self, **style)


@dataclass
class IMGUI:
    active: int | None = None
    hot: int | None = None
    focus: int | None = None
    tabindex_prev: int | None = None
    widgets: dict[int, Widget] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)


@contextlib.contextmanager
def render(ui: IMGUI, surface: pygame.Surface, get_styles=None):
    yield get_renderer(ui, surface, get_styles)
    ui.hot = None
    if not pygame.mouse.get_pressed()[0]:
        ui.active = None
    elif ui.active is None:
        ui.active = -1


def get_renderer(ui: IMGUI, surface: pygame.Surface, get_styles=None):

    def render(widget: Widget, **style) -> Widget:
        frame_info = inspect.stack()[1]
        widget_id = hash((frame_info.filename, frame_info.lineno))
        if callable(get_styles):
            style = get_styles(widget) | style
        with get_widget(ui, widget_id, widget, **style) as _widget:
            _widget.draw(surface, **style)
        return _widget.triggered

    return render


@contextlib.contextmanager
def get_widget(ui: IMGUI, widget_id: int, widget: Widget, **kwargs):
    widget.rect = get_widget_rect(widget, **kwargs)
    widget.triggered = False
    widget.pseudo_classes = set()

    if widget.rect.collidepoint(pygame.mouse.get_pos()):
        ui.hot = widget_id
        widget.pseudo_classes.add("hover")

    if ui.hot == widget_id and pygame.mouse.get_pressed()[0]:
        ui.active = widget_id
        widget.pseudo_classes.add("active")
        if widget.flags & CLICKABLE:
            widget.triggered = True

    if widget.flags & FOCUSABLE and ui.focus is None:
        ui.focus = widget_id
        widget.pseudo_classes.add("focus")

    if ui.focus == widget_id:
        widget.pseudo_classes.add("focus")
        handle_keys(widget, ui)

    yield widget

    if widget.flags & FOCUSABLE:
        ui.tabindex_prev = widget_id


def get_widget_rect(widget: Widget, **kwargs) -> pygame.Rect:
    if not widget.rect:
        widget.rect = pygame.Rect(0, 0, 0, 0)
        if isinstance(widget.value, (str, list)):
            font = kwargs.setdefault(
                "font",
                pygame.font.Font(None, kwargs.get("font_size", 20)),
            )
            widget.rect.size = font.size("".join(widget.value))
        if padding := kwargs.get("padding"):
            widget.rect, _ = add_padding(widget.rect, padding)
    if rect_kwargs := get_rect_attrs(kwargs):
        widget.rect = widget.rect.move_to(**rect_kwargs)
    return widget.rect


def draw_widget_background(surface: pygame.Surface, widget: Widget, **style) -> None:
    if widget.flags & HAS_BACKGROUND and widget.rect:
        color = style.get(
            "background_color",
            "white" if "active" in widget.pseudo_classes else "black",
        )
        pygame.draw.rect(
            surface,
            color,
            widget.rect,
            width=0,
            border_radius=style.get("border_radius", 0),
        )


def draw_widget_border(surface: pygame.Surface, widget: Widget, **style) -> None:
    if widget.flags & HAS_BORDER and widget.rect:
        pygame.draw.rect(
            surface,
            style.get("border_color", "white"),
            widget.rect,
            width=style.get("border_width", 1),
            border_radius=style.get("border_radius", 0),
        )


def draw_widget_focus(surface: pygame.Surface, widget: Widget, **style) -> None:
    if widget.rect:
        pygame.draw.rect(
            surface,
            style.get("focus_border_color", "red"),
            widget.rect.inflate(4, 4),
            width=style.get("focus_border_width", 4),
            border_radius=style.get("focus_border_radius", 0),
        )


def draw_widget_text(surface: pygame.Surface, widget: Widget, **style) -> None:
    if not widget.rect:
        return
    match widget.value:
        case str() | list():
            text = "".join(widget.value)
        case (str(text), _):
            pass
        case _:
            return None
    font = style.setdefault(
        "font",
        pygame.font.Font(None, style.get("font_size", 30)),
    )
    color = style.get("color", "white")
    label = font.render(text, True, color)
    rect = label.get_rect(center=widget.rect.center)
    match Align[style.get("align", "center")]:
        case Align.left:
            rect.left = widget.rect.left
        case Align.right:
            rect.right = widget.rect.right
        case _:
            rect.centerx = widget.rect.centerx
    match VAlign[style.get("valign", "middle")]:
        case VAlign.top:
            rect.top = widget.rect.top
        case VAlign.bottom:
            rect.bottom = widget.rect.bottom
        case _:
            rect.centery = widget.rect.centery
    _, rect = add_padding(rect, style.get("padding", 0))
    surface.blit(label, rect)


def handle_keys(widget: Widget, ui: IMGUI) -> None:
    for event in ui.events:
        if event.type != pg.KEYDOWN:
            continue
        if event.key == pg.K_TAB:
            if ui.focus and ui.widgets.get(ui.focus) == widget:
                ui.focus = None
                if event.mod & pg.KMOD_SHIFT:
                    ui.focus = ui.tabindex_prev
            # prevent this event from being processed by other widgets
            event.key = 0
        if widget.flags & EDITABLE and event.key == pg.K_BACKSPACE:
            widget.value[:] = widget.value[:-1]
            widget.triggered = True
        if widget.flags & EDITABLE and 32 <= event.key < 127 and len(widget.value) < 30:
            widget.value.append(event.unicode)
            widget.triggered = True
