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
        "background": pygame.Color("black"),
        "bold": False,
        "color": pygame.Color("white"),
        "font_name": None,
        "font_size": 30,
        "italic": False,
        "underline": False,
        "wrap_width": 0,
    }

    def __init__(self, text: str, **config) -> None:
        super().__init__()
        self.text = text
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
            num_lines = len(lines)
            if num_lines == 0:
                image = pygame.Surface((0, 0)).convert_alpha()
            elif num_lines == 1:
                image = self.font.render(
                    lines[0].text,
                    self.config["antialias"],
                    self.config["color"],
                    self.config["background"],
                )
                self.rect.size = lines[0].rect.size
            else:
                self.rect.width = max(line.rect.width for line in lines)
                self.rect.height = sum(line.rect.height for line in lines)
                image = pygame.Surface(self.rect.size).convert_alpha()
                if self.config["background"]:
                    image.fill(self.config["background"])
                align = Align[self.config["align"].upper()]
                for line in lines:
                    x_offset = round(align.value * (self.rect.width - line.rect.width))
                    image.blit(line.image, (line.rect.x + x_offset, line.rect.y))
            setattr(self, "_image", image)
        return getattr(self, "_image")

    def _wrap(self, text: str, width: int) -> list[Text]:
        lines = []
        line_height = self.config["line_height"]
        config = dict(**self.config)
        config["wrap_width"] = 0
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
