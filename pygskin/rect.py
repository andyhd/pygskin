from collections.abc import Sequence

from pygame import Rect

RECT_ATTRS = """
    x y
    top left bottom right
    topleft bottomleft topright bottomright
    midtop midleft midbottom midright
    center centerx centery
    size width height
    w h
""".strip().split()


def get_rect_attrs(d: dict) -> dict:
    return {k: v for k, v in d.items() if k in RECT_ATTRS}


def add_padding(
    rect: Rect,
    padding: int | Sequence[int] = 0,
) -> tuple[Rect, Rect]:
    match padding:
        case int(px):
            return rect.inflate(px * 2, px * 2), rect.move(px, px)

        case Sequence() as p if 1 <= len(p) <= 4 and all(isinstance(i, int) for i in p):
            try:
                it = iter(p)
                top = right = bottom = left = next(it)
                right = left = next(it)
                bottom = next(it)
                left = next(it)
            except StopIteration:
                pass
            return (
                rect.inflate(left + right, top + bottom).move_to(
                    top=rect.top - top, left=rect.left - left
                ),
                rect.move(left, top),
            )

    raise ValueError("Invalid padding")
