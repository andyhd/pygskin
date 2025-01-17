"""
A simple CSS-like stylesheet parser.
"""

import re
from dataclasses import dataclass
from dataclasses import field

SELECTOR = re.compile(r"(\A|[#.[]|::?)(\*|[a-zA-Z0-9-_]+)(?:=([^]]+))?")


@dataclass
class Selector:
    """A stylesheet selector."""

    tag: str | None = None
    id: str | None = None
    classes: list[str] = field(default_factory=list)
    attributes: dict[str, str] = field(default_factory=dict)
    pseudo_classes: list[str] = field(default_factory=list)


def get_styles(stylesheet: dict[str, dict], obj) -> dict:
    """
    Get the styles for an object from a stylesheet.

    >>> from typing import NamedTuple
    >>> Label = NamedTuple("Label", [("id", str), ("classes", list[str])])
    >>> label = Label("foo", ["bar"])
    >>> styles = {
    ...     "Label": {"font_family": "Arial", "font_size": 20, "color": "black"},
    ...     ".bar": {"bold": True, "color": "white"},
    ...     "#foo": {"color": "red"},
    ... }
    >>> get_styles(styles, label)
    {'font_family': 'Arial', 'font_size': 20, 'color': 'red', 'bold': True}
    """
    rulesets = ((parse_selector(k), v) for k, v in stylesheet.items())
    return {
        property: value
        for selector, declarations in sorted(rulesets, key=lambda r: specificity(r[0]))
        for property, value in declarations.items()
        if match(selector, obj)
    }


def parse_selector(s: str) -> Selector:
    """
    Parse a CSS selector.

    >>> from dataclasses import astuple
    >>> astuple(parse_selector("*"))
    ('*', None, [], {}, [])
    >>> astuple(parse_selector("button#submit.btn.btn-primary[type=submit]"))
    ('button', 'submit', ['btn', 'btn-primary'], {'type': 'submit'}, [])
    """
    parts = re.findall(SELECTOR, s)
    selector = Selector()
    for prefix, part, value in parts:
        if prefix == "#":
            selector.id = part
        elif prefix == ".":
            selector.classes.append(part)
        elif prefix == "[":
            key = part
            selector.attributes[key] = value
        elif prefix == ":":
            selector.pseudo_classes.append(part)
        else:
            selector.tag = part
    return selector


def specificity(selector: Selector) -> tuple[int, int, int]:
    """
    Calculate the specificity of a CSS selector.

    >>> specificity((parse_selector("button#submit.btn.btn-primary[type=submit]")))
    (1, 3, 1)
    """
    return (
        1 if selector.id else 0,
        len(selector.classes) + len(selector.attributes) + len(selector.pseudo_classes),
        1 if selector.tag and selector.tag != "*" else 0,
    )


def match(selector: Selector, obj) -> bool:
    """
    Check if the selector matches the given element.

    >>> from typing import NamedTuple
    >>> Image = NamedTuple("Image", [("id", str), ("classes", list[str]), ("src", str)])
    >>> el = Image("foo", ["bar", "red"], "/")
    >>> match(parse_selector("#foo"), el)
    True
    >>> match(parse_selector(".bar"), el)
    True
    >>> match(parse_selector("[src=/]"), el)
    True
    >>> match(parse_selector("Image"), el)
    True
    >>> match(parse_selector("Image#foo.bar.red[src=/]"), el)
    True
    >>> match(parse_selector("Image.bar.blue"), el)
    False
    """
    obj_type = getattr(obj, "type", obj.__class__.__name__)
    return (
        (not selector.tag or selector.tag == "*" or obj_type == selector.tag)
        and (not selector.id or obj.id == selector.id)
        and all(cls in obj.classes for cls in selector.classes)
        and all(
            getattr(obj, key, None) == value
            for key, value in selector.attributes.items()
        )
    )
