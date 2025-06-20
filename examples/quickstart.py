import pygame as pg

import pygskin

ground_y = 400

# Define a player entity with components
class Player(pygskin.Entity):
    rect: pg.Rect = lambda: pg.Rect(0, 0, 32, 32).move_to(x=100, bottom=ground_y)
    velocity: pg.Vector2 = pg.Vector2

# Create a player instance
player = Player()

# Create systems to handle player movement and physics
@pygskin.system
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

@pygskin.system
def handle_jump(rect: pg.Rect, velocity: pg.Vector2, *, events):
    # Jump if the player is on the ground
    if (
        rect.bottom == ground_y
        and any(ev.type == pg.KEYDOWN and ev.key == pg.K_SPACE for ev in events)
    ):
        velocity.y = -15

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

if __name__ == "__main__":
    # Create the game window and start the game
    window = pg.Window(size=(800, 600), title="Pygskin Platformer Demo")
    pygskin.run_game(window, game_loop) 