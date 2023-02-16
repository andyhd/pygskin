from pathlib import Path

import pygame
from pygame import K_0, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_SPACE
from pygskin.dialogue import Dialogue
from pygskin.events import KeyDown
from pygskin.input import Input
from pygskin.window import Window


def test_dialogue():
    pygame.font.init()

    dialogue = Dialogue.load(Path(__file__).parent / "ray_first_meeting.yaml")

    with Window((800, 600), background="black") as window:

        window.event_map = {
            KeyDown(K_0): Input(dialogue.select_prompt, 0),
            KeyDown(K_1): Input(dialogue.select_prompt, 1),
            KeyDown(K_2): Input(dialogue.select_prompt, 2),
            KeyDown(K_3): Input(dialogue.select_prompt, 3),
            KeyDown(K_4): Input(dialogue.select_prompt, 4),
            KeyDown(K_5): Input(dialogue.select_prompt, 5),
            KeyDown(K_6): Input(dialogue.select_prompt, 6),
            KeyDown(K_7): Input(dialogue.select_prompt, 7),
            KeyDown(K_8): Input(dialogue.select_prompt, 8),
            KeyDown(K_SPACE): Input(dialogue.next_state, None),
        }

        while window.running:
            dt = window.tick()

            dialogue.update(dt)
            dialogue.draw(window.surface)


if __name__ == '__main__':
    test_dialogue()
