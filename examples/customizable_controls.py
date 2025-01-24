"""
Example of customizing keyboard controls.
"""

from functools import partial

from pygame import Event
from pygame.key import name as key_name
from pygame.locals import (
    K_DOWN,
    K_ESCAPE,
    K_LEFT,
    K_RIGHT,
    K_UP,
    KEYDOWN,
)
from pygame.window import Window

from pygskin import imgui
from pygskin import map_inputs_to_actions
from pygskin import run_game
from pygskin.imgui import button, label


DEFAULT_KEY_CONTROLS = {
    "up": Event(KEYDOWN, key=K_UP),
    "down": Event(KEYDOWN, key=K_DOWN),
    "left": Event(KEYDOWN, key=K_LEFT),
    "right": Event(KEYDOWN, key=K_RIGHT),
    "quit": Event(KEYDOWN, key=K_ESCAPE),
}


def main():
    """
    Customizable controls example.
    """
    gui = imgui.IMGUI()
    text = ""
    action_map = DEFAULT_KEY_CONTROLS.copy()
    get_actions = partial(map_inputs_to_actions, action_map)
    waiting_for_input = None

    def main_loop(screen, events, exit_):
        """Test function for the game loop."""
        nonlocal text, waiting_for_input

        screen.fill("black")

        for action in get_actions(events):
            text = action

            if action == "quit":
                exit_()

        if waiting_for_input:
            for event in events:
                if event.type == KEYDOWN:
                    action_map[waiting_for_input] = event
                    waiting_for_input = None
                    break

        with imgui.render(gui, screen) as render:
            render(imgui.label("Set Controls"), font_size=40, center=(400, 100))

            for i, (action, event) in enumerate(action_map.items()):
                if render(button(action), padding=[10], center=(300, 200 + i * 50)):
                    if not waiting_for_input:
                        action_map[action] = None
                        waiting_for_input = action
                if event:
                    render(
                        label(f"{key_name(event.key)}"),
                        center=(500, 200 + i * 50),
                    )

            render(imgui.label(text), font_size=30, center=(400, 500))

    return main_loop


if __name__ == "__main__":
    run_game(Window("Testing", (800, 600)), main())
