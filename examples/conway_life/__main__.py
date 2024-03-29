from __future__ import annotations

import random
from collections.abc import Iterator
from dataclasses import dataclass

import pygame

from pygskin.display import Display
from pygskin.events import KeyDown
from pygskin.events import MouseButtonDown
from pygskin.events import MouseButtonUp
from pygskin.events import MouseMotion
from pygskin.events import Quit
from pygskin.events import event_listener
from pygskin.grid import Grid
from pygskin.text import Text
from pygskin.window import Window


@dataclass
class Cell:
    alive: bool
    num_neighbours: int


class CellGrid(Grid):
    def __post_init__(self) -> None:
        super().__post_init__()
        self.cells = self.empty()

    def __getitem__(self, xy: tuple[int, int]) -> Cell:
        x, y = xy
        return self.cells[y][x]

    def __setitem__(self, xy: tuple[int, int], value: Cell) -> None:
        x, y = xy
        self.cells[y][x] = value

    def empty(self) -> list[list[Cell]]:
        return [[Cell(False, 0) for x in range(self.cols)] for y in range(self.rows)]

    def with_keys(self) -> Iterator[tuple[tuple[int, int], Cell]]:
        for xy in self:
            yield xy, self[xy]

    def neighbours(self, xy) -> Iterator[Cell]:
        for xy in super().neighbours(*xy, wrap=True):
            yield self[xy]


class World(pygame.sprite.Sprite):
    def __init__(self, grid: Grid, cell_size: tuple[int, int]) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.grid = grid
        self.grid.cell_size = cell_size
        self.rect = pygame.Rect((0, 0), grid.mapped_size)
        self.cells = CellGrid(*grid.size)
        self.surface = pygame.Surface(self.rect.size)
        self.image_generation = self.generation = 0

    def next_generation(self) -> None:
        next_gen = CellGrid(*self.grid.size)

        for xy, cell in self.cells.with_keys():
            alive = (cell.alive and 2 <= cell.num_neighbours <= 3) or (
                not cell.alive and cell.num_neighbours == 3
            )

            if alive:
                next_gen[xy].alive = alive
                # for neighbour in next_gen.neighbours(xy):
                #     neighbour.num_neighbours += 1
                x, y = xy
                rows = ((y - 1) % self.grid.rows, y, (y + 1) % self.grid.rows)
                cols = ((x - 1) % self.grid.cols, x, (x + 1) % self.grid.cols)
                for ny in rows:
                    for nx in cols:
                        if not (ny == y and nx == x):
                            next_gen[(nx, ny)].num_neighbours += 1

        self.cells = next_gen
        self.generation += 1

    def randomize(self) -> None:
        for _xy, cell in self.cells.with_keys():
            cell.alive = random.random() < 0.5

    def refresh(self) -> None:
        for xy, cell in self.cells.with_keys():
            cell.num_neighbours = sum(
                neighbour.alive for neighbour in self.cells.neighbours(xy)
            )
        self.image_generation = -1

    @property
    def image(self) -> pygame.Surface:
        if self.image_generation != self.generation:
            self.surface.fill("black")
            for xy, cell in self.cells.with_keys():
                if cell.alive:
                    pygame.draw.rect(self.surface, "white", self.grid.rect(xy))
            self.image_generation = self.generation
            label = Text(f"Generation: {self.generation}", background="black")
            label.image.set_alpha(196)
            label.rect.bottom = self.grid.mapped_size[1]
            self.surface.blit(label.image, label.rect)
        return self.surface


class Game(Window):
    def __init__(self) -> None:
        self.world = World(Grid(160, 160), cell_size=(5, 5))
        self.world.add(Display.sprites)

        super().__init__(size=self.world.rect.size, title="Conway's Life")

        self.state = {
            "paused": True,
            "painting": False,
            "world": self.world,
        }

        self.pause_label = Text(
            (
                "PAUSED\n"
                "\n"
                "P   - Toggle pause\n"
                "R   - Randomise world\n"
                "G   - Add a Gosper Gun\n"
                "C   - Clear world\n"
                "Esc - Quit\n"
                "\n"
                "While paused, you can draw\n"
                "with the mouse"
            ),
            background="blue",
            padding=(20, 20),
        )
        self.pause_label.image.set_alpha(127)
        self.pause_label.rect.center = self.world.rect.center
        self.pause_label.add(Display.sprites)

    def update(self):
        super().update(**self.state)
        if not self.state["paused"]:
            self.world.next_generation()

    @event_listener
    def quit(self, _: KeyDown.ESCAPE | Quit) -> None:
        self.running = False

    @event_listener
    def randomize(self, _: KeyDown.R) -> None:
        self.world.randomize()
        self.world.refresh()

    @event_listener
    def clear(self, _: KeyDown.C) -> None:
        self.world.cells = CellGrid(*self.world.grid.size)
        self.world.generation = 0

    @event_listener
    def toggle_pause(self, _: KeyDown.P) -> None:
        self.state["paused"] = not self.state["paused"]
        if self.state["paused"]:
            self.pause_label.add(Display.sprites)
        else:
            self.pause_label.kill()

    @event_listener
    def toggle_painting(self, event: MouseButtonDown | MouseButtonUp) -> None:
        if self.state["paused"]:
            self.state["painting"] = not self.state["painting"]

    @event_listener
    def paint(self, event: MouseMotion) -> None:
        if self.state["painting"]:
            cell_width, cell_height = self.world.grid.cell_size
            x = event.pos[0] // cell_width
            y = event.pos[1] // cell_height
            self.world.cells[(x, y)].alive = True
            self.world.refresh()

    @event_listener
    def gosper_gun(self, _: KeyDown.G) -> None:
        cells = (
            "......................................",
            ".........................O............",
            ".......................O.O............",
            ".............OO......OO............OO.",
            "............O...O....OO............OO.",
            ".OO........O.....O...OO...............",
            ".OO........O...O.OO....O.O............",
            "...........O.....O.......O............",
            "............O...O.....................",
            ".............OO.......................",
            "......................................",
        )
        for y, row in enumerate(cells):
            for x, cell in enumerate(row):
                self.world.cells[(x + 40, y + 40)].alive = cell == "O"
        self.world.refresh()


if __name__ == "__main__":
    Game().run()
