from __future__ import annotations

from enum import Enum

import pygame
from pygame import Rect


class Align(Enum):
    LEFT = 0
    CENTER = 0.5
    RIGHT = 1


class Text(pygame.sprite.Sprite):
    """
    Simple API for drawing text.

    >>> txt = Text("hello world!")
    >>> screen.blit(txt.image, txt.rect)
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
        self.config = dict(**Text.DEFAULTS)
        self.config.update(config)
        self.font = pygame.font.Font(
            self.config["font_name"],
            self.config["font_size"],
        )
        self.font.bold = self.config["bold"]
        self.font.italic = self.config["italic"]
        self.font.underline = self.config["underline"]
        self.config.setdefault("line_height", self.font.get_linesize())
        self.rect = Rect(0, 0, 0, 0)

    @property
    def image(self) -> pygame.Surface:
        if not hasattr(self, "_image"):
            lines = self._wrap(self.text, self.config["wrap_width"])
            bg_color = self.config["background"]
            num_lines = len(lines)
            if num_lines == 0:
                image = pygame.Surface((0, 0)).convert_alpha()
            elif num_lines == 1:
                image = self.font.render(
                    lines[0].text,
                    self.config["antialias"],
                    self.config["color"],
                    bg_color,
                ).convert_alpha()
                self.rect.size = lines[0].rect.size
            else:
                self.rect.width = max(line.rect.width for line in lines)
                self.rect.height = sum(line.rect.height for line in lines)
                image = pygame.Surface(self.rect.size).convert_alpha()
                if bg_color:
                    image.fill(bg_color)
                align = Align[self.config["align"].upper()]
                for line in lines:
                    x_offset = round(align.value * (self.rect.width - line.rect.width))
                    image.blit(line.image, (line.rect.x + x_offset, line.rect.y))
            image = self._pad(image)
            setattr(self, "_image", image)
        return getattr(self, "_image")

    def _wrap(self, text: str, width: int) -> list[Text]:
        lines = []
        line_height = self.config["line_height"]
        config = dict(**self.config)
        config["wrap_width"] = 0
        config["padding"] = 0
        while text:
            line, _, text = text.partition("\n")
            line, remainder = self._break_line(line, width)
            if remainder:
                text = remainder + "\n" + text
            line_width = self.font.size(line)[0]
            line = Text(line, **config)
            lines.append(line)
            line.rect = Rect(self.rect.x, self.rect.bottom, line_width, line_height)
            self.rect.width = max(self.rect.width, line_width)
            self.rect.height += line_height
        return lines

    def _break_line(self, line: str, width: int) -> tuple[str, str]:
        if width > 0:
            last_break = 0
            for i, char in enumerate(line):
                if not self._breaking(char):
                    continue
                if self.font.size(line[:i])[0] > width:
                    return line[:last_break], line[last_break + 1 :]
                last_break = i
            else:
                if self.font.size(line)[0] > width:
                    return line[:last_break], line[last_break + 1 :]
        return line, ""

    def _breaking(self, char: str) -> bool:
        return char == " "

    def _pad(self, image: pygame.Surface) -> pygame.Surface:
        padding = self.config["padding"]
        if padding:
            try:
                padding = iter(padding)
                pad_bottom = pad_top = next(padding)
                pad_left = pad_right = next(padding)
                pad_bottom = next(padding)
                pad_right = next(padding)
            except StopIteration:
                pass
            padding = pygame.Surface(
                (
                    self.rect.width + pad_left + pad_right,
                    self.rect.height + pad_top + pad_bottom,
                )
            ).convert_alpha()
            bg_color = self.config["background"]
            if bg_color:
                padding.fill(bg_color)
            padding.blit(image, (pad_left, pad_top))
            image = padding
            self.rect = image.get_rect()
        return image
