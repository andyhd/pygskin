from __future__ import annotations

from enum import Enum
from functools import cached_property
from typing import Callable, Iterable

import pygame


class Align(Enum):
    LEFT = 0
    CENTER = 0.5
    RIGHT = 1


class Text(pygame.sprite.Sprite):
    """
    Simple API for drawing text.

    eg:
        txt = Text('hello world!')
        screen.blit(txt.image, txt.rect)
    """

    DEFAULTS = {
        "align": "LEFT",
        "antialias": True,
        "background": None,
        "bold": False,
        "color": pygame.Color("white"),
        "font_name": None,
        "font_size": 30,
        "italic": False,
        "underline": False,
        "wrap_width": 0,
        "padding": None,
    }

    def __init__(self, text: str, **config) -> None:
        super().__init__()
        self.text = text

        if not pygame.font.get_init():
            pygame.font.init()

        self.__dict__.update(Text.DEFAULTS)
        self.__dict__.update(config)

        self.align = Align[self.align.upper()].value
        self.font = pygame.font.Font(self.font_name, self.font_size)
        self.font.bold = self.bold
        self.font.italic = self.italic
        self.font.underline = self.underline
        self.__dict__.setdefault("line_height", self.font.get_linesize())

        self._breaking_chars = [" "]

    @cached_property
    def image(self) -> pygame.Surface:

        # render lines
        images = []
        rects = []
        width, height = 0, 0
        for line in wrap(
            self.text,
            lambda s: self.wrap_width and self.font.size(s)[0] > self.wrap_width
        ):
            image = self.font.render(line, self.antialias, self.color)
            rect = image.get_rect(top=height)
            width = max(width, rect.width)
            height += rect.height
            images.append(image)
            rects.append(rect)

        # horizontally align and apply padding
        size, (offset_x, offset_y) = pad((width, height), self.padding)
        for rect in rects:
            rect.move_ip(round(self.align * (width - rect.width)) + offset_x, offset_y)

        # blit onto background colour
        image = pygame.Surface(size).convert_alpha()
        image.fill(self.background or (0, 0, 0, 0))
        image.blits(zip(images, rects))

        return image

    @cached_property
    def rect(self) -> pygame.Rect:
        return self.image.get_rect()


def wrap(
    text: str,
    should_wrap: Callable[[str], int] = len,
    break_words_at: str = " ",
) -> list[str]:

    if not text:
        return []

    line, _, text = text.partition("\n")

    if not should_wrap(line):
        return [line] + wrap(text, should_wrap, break_words_at)

    last_word_end = 0
    remainder = ""

    # find last word break before max_width
    for i, char in enumerate(line):
        if char in break_words_at:
            if should_wrap(line[:i]):
                remainder = line[last_word_end + 1 :]
                line = line[:last_word_end]
                break
            last_word_end = i

    text = remainder + ("\n" if remainder and text else "") + text

    return [line] + wrap(text, should_wrap, break_words_at)


def pad(
    size: tuple[int, int],
    padding: Iterable[int] | None
) -> tuple[tuple[int, int], tuple[int, int]]:
    width, height = size
    pad_left = pad_top = 0

    if padding:
        try:
            padding = iter(padding)
            pad_top = pad_right = pad_bottom = pad_left = next(padding)
            pad_right = pad_left = next(padding)
            pad_bottom = next(padding)
            pad_left = next(padding)
        except StopIteration:
            pass

        width += pad_left + pad_right
        height += pad_top + pad_bottom

    return (width, height), (pad_left, pad_top)
