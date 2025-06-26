"""Immediate Mode GUI (IMGUI) system for Pygskin.

## Overview

Provides lightweight UI widgets that can be created and rendered each frame.
The system handles state management, event processing, and rendering automatically.

## Tutorial

### 1. Basic Setup

First, import the necessary components:

```python
import pygame
from pygskin import imgui, button, label
```

Initialize Pygame and create a window:

```python
window = pygame.Window("IMGUI Demo", (800, 600))
```

### 2. Creating a Simple UI

Create a basic game loop with a label and button:

```python
ui = imgui()

def game_loop(surface, events, quit_game):
    surface.fill("black")

    with ui(surface, events) as render:
        render(label("Hello World!"), center=(400, 100))
        if render(button("Click me"), center=(400, 200)):
            print("Button clicked!")

    if any(e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE for e in events):
        quit_game()

pygskin.run_game(window, game_loop)
```

### 3. Handling User Input

Create interactive widgets like text fields:

```python
ui = imgui()
text = list("Edit me")  # Textfields use mutable lists

def game_loop(surface, events, quit_game):
    surface.fill("black")

    with ui(surface, events) as render:
        render(label("Enter text:"), center=(400, 100))
        render(textfield(text), size=(300, 40), center=(400, 150))
        render(label(''.join(text)), center=(400, 200))
```

### 4. Styling Widgets

Apply custom styles using a stylesheet:

```python
from pygskin import get_styles

def stylesheet(widget):
    return get_styles(
        {
            "button": {
                "background_color": "blue",
                "border_color": "white",
                "font_size": 24
            },
            "label": {
                "color": "green",
                "font_size": 32
        },
        widget,
    )

gui = imgui(stylesheet)

def game_loop(surface, events, quit_game):
    surface.fill("black")
    with gui(surface, events) as render:
        render(label("Styled Text"), center=(400, 100))
        render(button("Styled Button"), center=(400, 200))
```

### 5. Advanced Widgets

Create radio button groups:

```python
ui = imgui()
choices = {"Option 1": 1, "Option 2": 2, "Option 3": 3}
selected = {"value": 1}

def game_loop(surface, events, quit_game):
    surface.fill("black")
    with ui(surface, events) as render:
        for i, (text, value) in enumerate(choices.items()):
            if render(radio(text),
                     checked=(selected["value"] == value),
                     x=400, y=200 + i*50):
                selected["value"] = value
```

## API Reference

Available Widgets:
- button(): Clickable button
- label(): Text display
- textfield(): Editable text input
- radio(): Selectable radio button
"""

import inspect
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
from enum import IntFlag
from enum import StrEnum
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


class Flag(IntFlag):
    CLICKABLE = 1
    EDITABLE = 2
    FOCUSABLE = 4
    SCROLLABLE = 8
    HAS_BORDER = 16
    HAS_BACKGROUND = 32
    HAS_SHADOW = 64


class PseudoClass(StrEnum):
    """Widget visual states.

    Attributes:
        HOVER: Mouse is over widget
        ACTIVE: Widget is being clicked/activated
        FOCUS: Widget has keyboard focus
    """

    HOVER = "hover"
    ACTIVE = "active"
    FOCUS = "focus"


@dataclass
class Widget:
    """UI widget container.

    Args:
        value: The widget's current value
        type: Widget type ('button', 'label', etc.)
        flags: Behavior flags (Flag enum)
        id: Optional unique identifier
        classes: CSS-like class names for styling
        rect: Widget position and size
        pseudo_classes: Current visual states
    """

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
    """Create a text label widget.

    Args:
        text: Label text
        **kwargs: Additional widget properties

    Returns:
        Widget: Configured label widget
    """
    return Widget(text, type="label", **kwargs)


def button(text: str | list[str], **kwargs) -> Widget:
    """Create a clickable button widget.

    Args:
        text: Button label text
        **kwargs: Additional widget properties

    Example:
    ```python
    render(button("Submit", id="submit-btn"))
    ```

    Returns:
        Widget: Configured button widget
    """
    return Widget(
        text,
        flags=Flag.CLICKABLE | Flag.FOCUSABLE | Flag.HAS_BORDER | Flag.HAS_BACKGROUND,
        type="button",
        **kwargs,
    )


def textfield(value: list[str], **kwargs) -> Widget:
    """Create an editable text input widget.

    Args:
        value: Initial text content (as mutable list)
        **kwargs: Additional widget properties

    Returns:
        Widget: Configured textfield widget
    """
    return Widget(
        value,
        flags=Flag.EDITABLE | Flag.FOCUSABLE | Flag.HAS_BORDER | Flag.HAS_BACKGROUND,
        type="textfield",
        **kwargs,
    )


def radio(value: str | list[str], **kwargs) -> Widget:
    """Create a radio button widget.

    Args:
        value: Radio button label
        **kwargs: Additional widget properties

    Returns:
        Widget: Configured radio button widget
    """
    return Widget(
        value,
        flags=Flag.CLICKABLE | Flag.FOCUSABLE | Flag.HAS_BACKGROUND,
        type="radio",
        **kwargs,
    )


@dataclass
class UIState:
    active: int | None = None
    focus: int | None = None
    tabindex_prev: int | None = None
    events: list[Event] = field(default_factory=list)


def update_widget_rect(widget: Widget, style: dict) -> None:
    rect = widget.rect or Rect(0, 0, 0, 0)
    if not rect:
        if text := get_widget_text(widget):
            font = style.setdefault("font", Font(None, style.get("font_size", 30)))
            rect.size = font.size(text)
        if padding := style.get("padding"):
            rect, _ = add_padding(rect, padding)
        if rect_kwargs := get_rect_attrs(style):
            widget.rect = rect.move_to(**rect_kwargs)


def click(event: Event) -> bool:
    return event.type == pg.MOUSEBUTTONDOWN and event.button == 1


def handle_mouse_events(widget: Widget, widget_id: int, ui: UIState) -> bool:
    if widget.rect.collidepoint(pygame.mouse.get_pos()):
        widget.pseudo_classes.add(PseudoClass.HOVER)

        if clicks := list(filter(click, ui.events)):
            ui.active = widget_id
            widget.pseudo_classes.add(PseudoClass.ACTIVE)
            if widget.flags & Flag.CLICKABLE:
                [setattr(e, "button", 0) for e in clicks]
                return True

    return False


def handle_keyboard_events(widget: Widget, ui: UIState) -> None:
    for e in [e for e in ui.events if e.type == pg.KEYDOWN]:
        if e.key == pg.K_TAB:
            ui.focus = ui.tabindex_prev if e.mod & pg.KMOD_SHIFT else None
            e.key = 0

        if widget.flags & Flag.EDITABLE:
            if e.key == pg.K_BACKSPACE:
                widget.value[:] = widget.value[:-1]
            elif 32 <= e.key < 127 and len(widget.value) < 30:
                widget.value.append(e.unicode)


def manage_focus(widget: Widget, widget_id: int, ui: UIState) -> None:
    if widget.flags & Flag.FOCUSABLE and ui.focus is None:
        ui.focus = widget_id

    if ui.focus == widget_id:
        widget.pseudo_classes.add(PseudoClass.FOCUS)
        handle_keyboard_events(widget, ui)

    if widget.flags & Flag.FOCUSABLE:
        ui.tabindex_prev = widget_id


def imgui(get_styles: Callable | None = None) -> Callable:
    """
    Get a context manager for rendering immediate mode GUI widgets and handling events.
    """
    ui = UIState()
    get_styles = get_styles if callable(get_styles) else lambda _: {}

    @contextmanager
    def imgui_ctx(surface: Surface, events: list[Event]) -> Iterator[Callable]:
        ui.events = events

        def render(widget: Widget, **style) -> bool:
            # get caller location to ensure unique widget IDs
            frames = inspect.getouterframes(inspect.currentframe())
            caller = next(frm for frm in frames if frm.filename != __file__)
            widget_id = hash((caller.filename, caller.lineno, id(widget.value)))

            style = get_styles(widget) | style
            update_widget_rect(widget, style)
            triggered = handle_mouse_events(widget, widget_id, ui)
            manage_focus(widget, widget_id, ui)
            draw_widget(widget, surface=surface, **style)
            return triggered

        yield render

        if not pygame.mouse.get_pressed()[0]:
            ui.active = None
        elif ui.active is None:
            ui.active = -1

    return imgui_ctx


__all__ = [
    "imgui",
    "button",
    "label",
    "radio",
    "textfield",
]
