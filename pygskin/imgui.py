"""Immediate Mode GUI (IMGUI) system for Pygskin."""

import inspect
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import contextmanager
from contextlib import suppress
from dataclasses import dataclass
from dataclasses import field
from enum import IntEnum
from enum import IntFlag
from enum import StrEnum
from itertools import count
from typing import Any
from typing import NamedTuple

import pygame
import pygame.locals as pg
from pygame import Event
from pygame import Font
from pygame import FRect
from pygame import Rect
from pygame import Surface
from pygame import Vector2

from pygskin.direction import Direction
from pygskin.rect import align_rect
from pygskin.rect import get_rect_attrs

HORIZONTAL = Direction.HORIZONTAL
VERTICAL = Direction.VERTICAL
Align = IntEnum("Align", [("LEFT", 0), ("CENTER", 1), ("RIGHT", 2), ("JUSTIFY", -1)])
VAlign = IntEnum("VAlign", [("TOP", 0), ("MIDDLE", 1), ("BOTTOM", 2), ("JUSTIFY", -1)])


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
        children: Child widgets
    """

    value: Any
    type: str
    flags: int = 0
    id: str | None = None
    classes: list[str] = field(default_factory=list)
    rect: Rect = field(default_factory=lambda: Rect(0, 0, 0, 0))
    _min: Vector2 = field(default_factory=Vector2)
    _max: Vector2 = field(default_factory=Vector2)
    pseudo_classes: set[PseudoClass] = field(default_factory=set)
    children: list[dict] = field(default_factory=list)

    def __repr__(self) -> str:
        value = get_widget_text(self) or self.value
        container_info = f", children={len(self.children)}" if self.children else ""
        return f"{self.type}({value!r}, {self.rect}{container_info})"


def draw_widget(widget: Widget, *, surface: Surface, style: dict) -> None:
    if widget.rect:
        if PseudoClass.FOCUS in widget.pseudo_classes:
            draw_focus(surface, widget, style)
        if "background_color" in style:
            draw_background(surface, widget, style)
        if widget.type == "radio":
            draw_radio_button(surface, widget, style)
        if style.get("border_width", 0):
            draw_border(surface, widget, style)
        if text := get_widget_text(widget):
            draw_text(surface, text, widget, style)


def draw_focus(surface: Surface, widget: Widget, style: dict) -> None:
    pygame.draw.rect(
        surface,
        style.get("focus_border_color", "red"),
        widget.rect.inflate(4, 4),
        width=style.get("focus_border_width", 4),
        border_radius=style.get("focus_border_radius", 0),
    )


def draw_background(surface: Surface, widget: Widget, style: dict) -> None:
    color = style.get(
        "background_color",
        "white" if PseudoClass.ACTIVE in widget.pseudo_classes else "black",
    )
    try:
        bg = Surface(widget.rect.size, flags=pg.SRCALPHA)
        pygame.draw.rect(
            bg,
            color,
            widget.rect.move_to(topleft=(0, 0)),
            width=0,
            border_radius=style.get("border_radius", 0),
        )
        surface.blit(bg, widget.rect)
    except pygame.error:
        pass


def draw_border(surface: Surface, widget: Widget, style: dict) -> None:
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


def draw_text(surface: Surface, text: str, widget: Widget, style: dict) -> None:
    font_size = style.get("font_size", 20)
    font = style.get("font", Font(None, font_size))
    color = style.get("color", "white")
    pad = padding(*style.get("padding", [0]))
    text_img = font.render(
        text,
        True,
        color,
        wraplength=widget.rect.width - pad.left - pad.right,
    )
    text_rect = text_img.get_rect(center=widget.rect.center)
    content_rect = widget.rect.move_to(
        left=widget.rect.left + pad.left,
        top=widget.rect.top + pad.top,
        width=widget.rect.width - pad.left - pad.right,
        height=widget.rect.height - pad.top - pad.bottom,
    )
    align_rect(
        text_rect,
        content_rect,
        style.get("align", "center"),
        style.get("valign", "middle"),
    )
    if widget.type == "radio":
        text_rect.x += font_size * 1.5  # Offset for radio button
        text_rect.width -= font_size * 1.5
    surface.blit(text_img, text_rect)


def draw_radio_button(surface: Surface, widget: Widget, style: dict) -> None:
    pad = padding(*style.get("padding", [0]))
    font_size = style.get("font_size", 20)
    box = widget.rect.move_to(
        x=widget.rect.x + pad.left,
        y=widget.rect.y + pad.top - font_size // 2,
        width=font_size,
        height=font_size,
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
    root: Widget | None = None
    layout_cache: dict[int, Rect] = field(default_factory=dict)


def handle_mouse_events(widget: Widget, widget_id: int, ui: UIState) -> bool:
    if widget.rect.collidepoint(pygame.mouse.get_pos()):
        widget.pseudo_classes.add(PseudoClass.HOVER)

        if pygame.mouse.get_pressed()[0]:
            ui.active = widget_id
            widget.pseudo_classes.add(PseudoClass.ACTIVE)
            if widget.flags & Flag.CLICKABLE:
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


def get_style_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Extract style-related keys from kwargs."""
    return {
        k: v
        for k, v in kwargs.items()
        if k
        in {
            "background_color",
            "border_color",
            "border_radius",
            "border_width",
            "checked",  # XXX should be pseudo-class
            "color",
            "focus_border_color",
            "focus_border_radius",
            "focus_border_width",
            "font",
            "font_size",
            "padding",
            "spacing",
            "align",
            "valign",
            "direction",
            "grow",
            "shrink",
        }
    } | get_rect_attrs(kwargs)


debug_widget_id_seq = count()
debug_widget_id = {}


def imgui(get_styles: Callable | None = None) -> Callable:
    """
    Get a context manager for rendering immediate mode GUI widgets and handling events.
    """
    ui = UIState()
    get_styles = get_styles if callable(get_styles) else lambda _: {}

    @contextmanager
    def imgui_ctx(
        surface: Surface, events: list[Event], **kwargs
    ) -> Iterator[Callable]:
        ui.events = events
        ui.root = Widget(0, type="root", rect=surface.get_rect(), **kwargs)
        container_stack = [ui.root]
        container_count = count()

        def render(widget: Widget, **render_kwargs) -> bool:
            # get caller location to ensure unique widget IDs
            frames = inspect.getouterframes(inspect.currentframe())
            caller = next(frm for frm in frames if frm.filename != __file__)
            widget_id = hash((caller.filename, caller.lineno, id(widget.value)))

            if widget_id in ui.layout_cache:
                widget.rect = ui.layout_cache[widget_id]

            style = get_styles(widget) | get_style_kwargs(render_kwargs)

            if rect_attrs := get_rect_attrs(style):
                widget.rect.move_to(**rect_attrs)
            if "max_width" in render_kwargs:
                widget._max[0] = render_kwargs["max_width"]

            if container_stack:
                container_stack[-1].children.append((widget_id, widget, style))

            triggered = handle_mouse_events(widget, widget_id, ui)
            manage_focus(widget, widget_id, ui)
            draw_widget(widget, surface=surface, style=style)
            return triggered

        @contextmanager
        def container(**kwargs) -> Iterator[None]:
            widget = Widget(
                next(container_count),
                type=kwargs.pop("type", "box"),
                flags=kwargs.pop("flags", 0),
                id=kwargs.pop("id", None),
                classes=kwargs.pop("classes", []),
                rect=kwargs.pop("rect", Rect(0, 0, 0, 0)),
            )
            render(widget, **kwargs)
            container_stack.append(widget)
            yield
            container_stack.pop()

        render.horizontally = lambda **kwargs: container(
            type="container", direction=HORIZONTAL, **kwargs
        )
        render.vertically = lambda **kwargs: container(
            type="container", direction=VERTICAL, **kwargs
        )

        yield render

        if not ui.layout_cache:
            layout_widgets(ui.root, get_styles(ui.root) | get_style_kwargs(kwargs))

            def cache_rects(widget_id: int, widget: Widget) -> None:
                ui.layout_cache[widget_id] = widget.rect.copy()
                for child_id, child, _ in widget.children:
                    cache_rects(child_id, child)

            cache_rects(0, ui.root)

        if not pygame.mouse.get_pressed()[0]:
            ui.active = None
        elif ui.active is None:
            ui.active = -1

    return imgui_ctx


class Padding(NamedTuple):
    top: int = 0
    right: int = 0
    bottom: int = 0
    left: int = 0


def padding(*widths: int) -> Padding:
    with suppress(StopIteration):
        it = iter(widths)
        top = right = bottom = left = next(it)
        right = left = next(it)
        bottom = next(it)
        left = next(it)
    return Padding(top, right, bottom, left)


def get_widget_text_size(
    widget: Widget, style: dict | None = None
) -> tuple[Rect, tuple[int, int]]:
    if not (text := get_widget_text(widget)):
        return Rect(0, 0, 0, 0), (0, 0)

    style = style or {}
    font = style.get("font", Font(None, style.get("font_size", 20)))
    text_size = font.size(text)
    longest_word = sorted(text.split(), key=len)[-1]
    return Rect((0, 0), text_size), font.size(longest_word)


def fit_contents(
    widget: Widget, axis: Direction = VERTICAL, style: dict | None = None
) -> None:
    """Resize a widget to fit its contents.

    >>> import pygame
    >>> pygame.init()
    (...)
    >>> widget = Widget(None, type="box", children=[
    ...     (0, Widget("foo bar quux", type="label"), {}), # 80x14
    ...     (1, Widget(None, type="box", rect=Rect(0, 0, 100, 0)), {}),
    ...     (2, Widget(None, type="box", children=[
    ...         (3, Widget("hello world", type="label"), {}) # 70x14
    ...     ]), {}),
    ... ])
    >>> fit_contents(widget, HORIZONTAL, {"direction": HORIZONTAL})
    >>> widget.rect
    Rect(0, 0, 250, 0)
    >>> fit_contents(widget, VERTICAL, {"direction": HORIZONTAL})
    >>> widget.rect
    Rect(0, 0, 250, 14)
    """
    axis_pos = int(axis == VERTICAL)
    axis_len = axis_pos + 2
    rect = widget.rect
    _min = widget._min
    style = style or {}

    # recurse into children
    for _, child, child_style in widget.children:
        fit_contents(child, axis, child_style)

    # fixed size
    rect_attrs = get_rect_attrs(style)
    styled_rect = rect.move_to(**rect_attrs) if rect_attrs else rect.copy()
    if rect[axis_len] or styled_rect[axis_len]:
        rect[axis_len] = rect[axis_len] or styled_rect[axis_len]
        _min[axis_pos] = widget._max[axis_pos] = rect[axis_len]
        return

    pad = padding(*style.get("padding", [0]))
    rect[axis_len] += pad[axis_pos] + pad[axis_len]

    # text widget
    preferred, text_min = get_widget_text_size(widget, style)
    if preferred[axis_len]:
        rect[axis_len] += preferred[axis_len]
        _min[axis_pos] = max(_min[axis_pos], text_min[axis_pos])
        return

    if not widget.children:
        return

    # container widget
    if style.get("direction", VERTICAL) == axis:
        rect[axis_len] += sum(child.rect[axis_len] for _, child, _ in widget.children)
        rect[axis_len] += max(0, len(widget.children) - 1) * style.get("spacing", 0)
        _min[axis_pos] = sum(child._min[axis_pos] for _, child, _ in widget.children)
    else:
        rect[axis_len] += max(child.rect[axis_len] for _, child, _ in widget.children)
        _min[axis_pos] = max(child._min[axis_pos] for _, child, _ in widget.children)


def flex_children(widget: Widget, axis=VERTICAL, style: dict | None = None) -> None:
    """Resize widget children to flexibly fill available space.

    >>> import pygame
    >>> pygame.init()
    (...)
    >>> widget = Widget(2, type="box")
    >>> parent = Widget(0, type="box", rect=Rect(0, 0, 500, 200))
    >>> parent.children.extend([
    ...     (1, Widget(1, type="box", rect=Rect(0, 0, 100, 20)), {}),
    ...     (2, widget, {"grow": HORIZONTAL | VERTICAL}),
    ... ])
    >>> flex_children(parent, HORIZONTAL, {"direction": HORIZONTAL})
    >>> widget.rect
    Rect(0, 0, 400, 0)
    >>> flex_children(parent, VERTICAL, {"direction": HORIZONTAL})
    >>> widget.rect
    Rect(0, 0, 400, 200)
    """
    axis_pos = int(axis == VERTICAL)
    axis_len = axis_pos + 2
    style = style or {}
    pad = padding(*style.get("padding", [0]))
    total_flex = widget.rect[axis_len] - pad[axis_pos] - pad[axis_len]
    widget_direction = style.get("direction", VERTICAL)
    if widget.children and axis == widget_direction:
        total_flex -= sum(child.rect[axis_len] for _, child, _ in widget.children)
        total_flex -= max(0, len(widget.children) - 1) * style.get("spacing", 0)
    sign = 1 if total_flex > 0 else -1

    to_flex = [
        child
        for _, child, child_style in widget.children
        if (axis & child_style.get("grow", 0)) or (axis & child_style.get("shrink", 0))
    ]

    while to_flex and abs(total_flex) > 0:
        # grow the smallest widgets or shrink the largest ones
        sizes = sorted({w.rect[axis_len] for w in to_flex}, reverse=sign < 0)
        first, second, *_ = sizes + [sizes[-1]]
        delta = max(1, abs(second - first) or abs(total_flex // len(to_flex)))

        for child in to_flex.copy():
            limit = child._max[axis_pos] if sign > 0 else child._min[axis_pos]
            to_limit = abs(limit - child.rect[axis_len]) if limit else float("inf")

            # on-axis: total_flex is the pool of space to distribute
            if widget_direction == axis and child.rect[axis_len] == first:
                flex_amt = min(delta, abs(total_flex), to_limit)
                total_flex -= flex_amt * sign
                child.rect[axis_len] += flex_amt * sign
                if limit and child.rect[axis_len] == limit:
                    to_flex.remove(child)

            # off-axis: total_flex is the target size for the child
            elif widget_direction != axis:
                flex_amt = min(total_flex - child.rect[axis_len], to_limit)
                child.rect[axis_len] += flex_amt * sign
                to_flex.remove(child)

    # recursively flex children
    for _, child, child_style in widget.children:
        flex_children(child, axis, child_style)


def wrap_text(widget: Widget, style: dict | None = None) -> None:
    """Wrap text in widgets to fit width.

    >>> import pygame
    >>> pygame.init()
    (...)
    >>> text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    >>> label = (1, Widget(text, type="label", rect=Rect(0, 0, 100, 0)), {})
    >>> widget = Widget(None, type="box", children=[label])
    >>> wrap_text(widget, {})
    >>> label[1]._min[1]
    60.0
    """
    style = style or {}
    for _, child, child_style in widget.children:
        if child.children:
            wrap_text(child, child_style)

        elif text := get_widget_text(child):
            font = child_style.get("font", Font(None, child_style.get("font_size", 20)))
            img = font.render(text, True, "red", wraplength=child.rect.width)
            child._min[1] = img.get_height()


def position_children(widget: Widget, style: dict | None = None) -> None:
    """Position children within a widget based on alignment and padding.

    >>> import pygame
    >>> pygame.init()
    (...)
    >>> box1 = Widget("Child 1", type="label", rect=Rect(0, 0, 100, 50))
    >>> box2 = Widget("Child 2", type="label", rect=Rect(0, 0, 150, 50))
    >>> widget = Widget(None, type="box", rect=Rect(0, 0, 800, 600), children=[
    ...     (1, box1, {}), (2, box2, {}),
    ... ])
    >>> position_children(widget)
    >>> box1.rect
    Rect(0, 0, 100, 50)
    >>> box2.rect
    Rect(0, 50, 150, 50)
    """
    style = style or {}
    axis = style.get("direction", VERTICAL)
    axis_pos = int(axis == VERTICAL)
    axis_len = axis_pos + 2
    cross_axis_pos = 1 - axis_pos
    cross_axis_len = cross_axis_pos + 2
    pad = padding(*style.get("padding", [0]))
    space = widget.rect[axis_len]
    space -= pad[axis_pos] + pad[axis_len]
    spacing = style.get("spacing", 0)
    if widget.children:
        space -= sum(child.rect[axis_len] for _, child, _ in widget.children)
        space -= max(0, len(widget.children) - 1) * spacing
    alignment = Align[style.get("align", "left").upper()]
    cross_alignment = VAlign[style.get("valign", "top").upper()]
    if axis == VERTICAL:
        alignment, cross_alignment = cross_alignment, alignment

    # position children along layout axis
    alignment_offset = max(0, space * max(0, alignment.value) / 2)
    pos = widget.rect[axis_pos] + pad[axis_pos] + alignment_offset
    for _, child, _ in widget.children:
        child.rect[axis_pos] = pos
        pos += child.rect[axis_len] + spacing

    # position children along cross axis (individually)
    for _, child, _ in widget.children:
        space = (
            widget.rect[cross_axis_len]
            - child.rect[cross_axis_len]
            - pad[cross_axis_pos]
            - pad[cross_axis_len]
        )
        alignment_offset = max(0, space * max(0, cross_alignment.value) / 2)
        child.rect[cross_axis_pos] = (
            widget.rect[cross_axis_pos] + pad[cross_axis_pos] + alignment_offset
        )

    # recursively position children
    for _, child, style in widget.children:
        position_children(child, style)


def layout_widgets(container: Widget, style: dict | None = None) -> None:
    """Arrange widgets within a container using flexbox-like properties.

    >>> import pygame
    >>> pygame.init()
    (...)
    >>> root = Widget(0, type="box", rect=Rect(0, 0, 500, 200))
    >>> root.children.extend([
    ...     (1, Widget("foo bar quux", type="label"), {"grow": HORIZONTAL}),
    ...     (2, Widget(1, type="box"), {"grow": HORIZONTAL | VERTICAL}),
    ...     (3, Widget(2, type="box", children=[
    ...         (4, Widget("hello world", type="label"), {}),
    ...     ]), {}),
    ... ])
    >>> layout_widgets(root, {"direction": HORIZONTAL})
    >>> for _, child, _ in root.children:
    ...     print(child.rect)
    Rect(0, 0, 215, 14)
    Rect(215, 0, 215, 200)
    Rect(430, 0, 70, 13)
    """
    style = style or {}
    fit_contents(container, HORIZONTAL, style)
    flex_children(container, HORIZONTAL, style)
    wrap_text(container, style)
    fit_contents(container, VERTICAL, style)
    flex_children(container, VERTICAL, style)
    position_children(container, style)


__all__ = [
    "imgui",
    "button",
    "label",
    "radio",
    "textfield",
]
