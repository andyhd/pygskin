"""
A lightweight, modern game development library built on top of Pygame.

## Overview

Pygskin provides a collection of tools and utilities to make game development
with Pygame more enjoyable and productive. It offers a clean, intuitive API
while maintaining the flexibility and simplicity of Pygame.

## Requirements

- Python 3.13 or higher
- [Pygame CE](https://pyga.me) 2.5.2

## Quick Start

Let's create a simple platformer game to get started with Pygskin! We'll build a
game where you can control a character that can move left, right, and jump. This
tutorial will walk you through some of the basic concepts of Pygskin while
creating something fun.

First, let's set up our imports. We'll use Pygame (imported as 'pg' for brevity)
and Pygskin:

```python
import pygame as pg
import pygskin
```

For our simple platformer, we'll need a ground for our character to walk on.
We'll position it 400 pixels from the top of the screen, which gives us plenty
of room for jumping:

```python
ground_y = 400
```

Now, let's create our player character! In Pygskin, we use an Entity Component
System (ECS) to organize our game objects. This might sound complex, but it's
actually quite simple - think of an Entity as a game object (like our player)
and components as the properties that define what that object can do.

For our player, we'll create a class that inherits from `pygskin.Entity`. We'll
give it two components:
- A `rect` component that defines where the player is on screen (we'll start
  with a 32x32 pixel square)
- A `velocity` component that will help us handle movement

The `rect` component uses a lambda function to create a rectangle positioned at
x=100 and sitting on our ground. The `velocity` component is a simple Vector2
that will store our movement speed:

```python
class Player(pygskin.Entity):
    rect: pg.Rect = lambda: pg.Rect(0, 0, 32, 32).move_to(x=100, bottom=ground_y)
    velocity: pg.Vector2 = pg.Vector2

# Create a player instance
player = Player()
```

Next, we'll create a system to handle player movement. In Pygskin, systems are
functions that define how entities behave. We'll create a system that responds
to keyboard input to move our player left and right. The `@system` decorator
tells Pygskin to automatically call this function for any entity that has a
velocity component.

The `events` parameter (marked with `*` to make it keyword-only) will receive
all the input events from Pygame. We'll use these to detect when the player
presses the left or right arrow keys:

```python
@system
def handle_movement(rect: pg.Rect, velocity: pg.Vector2, *, events):
    for event in events:
        # Start moving left or right
        if event.type == pg.KEYDOWN and event.key == pg.K_LEFT:
            velocity.x = -5
        if event.type == pg.KEYDOWN and event.key == pg.K_RIGHT:
            velocity.x = 5

        # Stop moving if the key is released
        if event.type == pg.KEYUP and (
            (event.key == pg.K_LEFT and velocity.x < 0)
            or (event.key == pg.K_RIGHT and velocity.x > 0)
        ):
            velocity.x = 0

    rect.x += velocity.x
```

Now we need a game loop to tie everything together. The game loop is the heart
of our game - it runs every frame and handles:
- Processing input
- Updating game state
- Drawing everything to the screen

Our game loop receives three important parameters:
- `screen`: The Pygame surface we draw to
- `events`: The list of input events since the last frame
- `quit_game`: A function to safely exit the game

```python
def game_loop(screen, events, quit_game):
    # Quit the game if the escape key is pressed
    if any(event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE for event in events):
        quit_game()
    
    handle_movement(events=events)
    
    # Clear the screen with a light gray background
    screen.fill("gray70")
    # Draw our ground as a dark gray rectangle
    pg.draw.rect(screen, "gray30", pg.Rect(0, 400, 800, 200))
    # Draw our player as a red square
    pg.draw.rect(screen, "red", player.rect)
```

Finally, we create our game window and start the game! We'll make an 800x600
pixel window with a title:

```python
window = pg.Window(size=(800, 600), title="Pygskin Platformer Demo")
pygskin.run_game(window, game_loop)
```

At this point, you can run the game and move the red square left and right with
the arrow keys! But let's make it more interesting by adding a new system to
handle jumping. When the player presses the space bar and is on the ground,
we'll make them jump by giving them an upward velocity:

```python
@pygskin.system
def handle_jump(rect: pg.Rect, velocity: pg.Vector2, *, events):
    # Jump if the player is on the ground
    if (
        rect.bottom == ground_y
        and any(ev.type == pg.KEYDOWN and ev.key == pg.K_SPACE for ev in events)
    ):
        velocity.y = -15
```

We need to handle gravity and movement too! Let's create a physics system that:
- Applies gravity to pull the player down
- Updates the player's position based on their velocity
- Stops the player when they hit the ground

```python
@pygskin.system
def apply_physics(rect: pg.Rect, velocity: pg.Vector2):
    # Apply gravity
    velocity.y += 0.8

    # Update position
    rect.y += velocity.y

    # Simple ground collision
    if rect.bottom > ground_y:
        rect.bottom = ground_y
        velocity.y = 0
```

Finally, we update our game loop to include our new systems:

```python
def game_loop(screen, events, quit_game):
    # Quit the game if the escape key is pressed
    if any(event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE for event in events):
        quit_game()

    handle_movement(events=events)
    handle_jump(events=events)
    apply_physics()
    
    # Clear the screen
    screen.fill("gray70")
    # Draw ground
    pg.draw.rect(screen, "gray30", pg.Rect(0, 400, 800, 200))
    # Draw player
    pg.draw.rect(screen, "red", player.rect)
```

Now you have a fully functional platformer! You can:
- Move left and right with the arrow keys
- Jump with the space bar
- Quit the game with the escape key

Try running the game and experiment with the values (like jump height, movement
speed, and gravity) to see how they affect the gameplay!
"""

from pygskin import easing
from pygskin.animation import EasingFn
from pygskin.animation import LerpFn
from pygskin.animation import animate
from pygskin.animation import get_spritesheet_frames
from pygskin.assets import Assets
from pygskin.assets import load_music
from pygskin.camera import Camera
from pygskin.clock import Clock
from pygskin.clock import Timer
from pygskin.dialogue import iter_dialogue
from pygskin.direction import Direction
from pygskin.ecs import Entity
from pygskin.ecs import kill_entity
from pygskin.ecs import map_components
from pygskin.ecs import system
from pygskin.func import bind
from pygskin.game import run_game
from pygskin.gradient import make_color_gradient
from pygskin.imgui import IMGUI
from pygskin.imgui import button
from pygskin.imgui import label
from pygskin.imgui import radio
from pygskin.imgui import textfield
from pygskin.input import map_inputs_to_actions
from pygskin.lazy import lazy
from pygskin.parallax import scroll_parallax_layers
from pygskin.pubsub import channel
from pygskin.rect import add_padding
from pygskin.rect import align_rect
from pygskin.rect import get_rect_attrs
from pygskin.rect import grid
from pygskin.screen import ScreenFn
from pygskin.screen import screen_manager
from pygskin.shake import shake
from pygskin.sparse_array import SparseArray
from pygskin.spritesheet import spritesheet
from pygskin.spritestack import draw_sprite_stack
from pygskin.statemachine import statemachine
from pygskin.stylesheet import get_styles
from pygskin.surface import make_sprite
from pygskin.surface import rotate_surface
from pygskin.text import speech_duration
from pygskin.text import to_snakecase
from pygskin.tile import tile
from pygskin.utils import circle_path
from pygskin.vector import angle_between

__all__ = [
    "Assets",
    "Camera",
    "Clock",
    "Direction",
    "EasingFn",
    "Entity",
    "IMGUI",
    "LerpFn",
    "ScreenFn",
    "SparseArray",
    "Timer",
    "add_padding",
    "align_rect",
    "angle_between",
    "animate",
    "bind",
    "button",
    "channel",
    "circle_path",
    "draw_sprite_stack",
    "easing",
    "get_rect_attrs",
    "get_spritesheet_frames",
    "get_styles",
    "grid",
    "iter_dialogue",
    "kill_entity",
    "label",
    "lazy",
    "load_music",
    "make_color_gradient",
    "make_sprite",
    "map_components",
    "map_inputs_to_actions",
    "radio",
    "rotate_surface",
    "run_game",
    "screen_manager",
    "scroll_parallax_layers",
    "shake",
    "speech_duration",
    "spritesheet",
    "statemachine",
    "system",
    "textfield",
    "tile",
    "to_snakecase",
]
