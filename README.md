# Pygskin

A wrapper around Pygame

## `animation.py`
`KeyframeAnimation` maps time to key frames and allows lerping with easing
functions to interpolate frames.

`AnimationPlayer` start, stop, pause and resume animations

## `assets.py`
`Assets` provides attribute access to asset files and batch loading
Eg:
```python
assets = Assets()
display.blit(assets.player, (0, 0))
assets.player_spawn_sfx.play()
```
TODO - progress bar via custom events

## `clock.py`
ECS system for invoking callbacks on each frame
TODO - does this need to be a System?

## `dialogue.py`
`Dialogue` parses a YAML script into a branching dialogue state machine

## `direction.py`
`Direction` enum for simple up/down/left/right directions

## `display.py`
ECS system for drawing visible entities on the main display surface
TODO - does this need to be a system?

## `easing.py`
A selection of easing functions for use with interpolation

## `ecs.py`
A simple ECS system. Systems can be classes or decorated functions. Entities are
filtered using type hints or a function. Components can be anything.

## `events.py`
Event handlers are decorated functions, using type hints to register event types
to handle. Event types wrap standard Pygame events. Custom events. ECS system
dispatches events to handlers in entities.

## `gradient.py`
Generate horizontal or vertical gradient filled surfaces

## `grid.py`
Utility class for grids.

## `parallax.py`
Parallax scrolling
TODO - Use LayeredUpdates

## `particles.py`
Particle system with gravity, drag, etc
TODO - use OpenGL? prefill emitters

## `pubsub.py`
Pub/sub messages as function decorators - subscribed callbacks triggered on
function call

## `screen.py`
Screen manager state machine
TODO - transition animations (fade in/out, slide, wipe, etc)

## `spritesheet.py`
Spritesheet data structure from image and grid. Access individual
sprites by (row, col) tuple index or string keys.
TODO - spritesheet to animation

## `statemachine.py`
State machine utility class

## `text.py`
Generate surface from font (including bitmap font), with wrapping to width,
alignment, padding. Dynamic text sprites.
TODO - markdown? animation?

## `utils.py`
Image rotation function, misc

## `window.py`
Boilerplate game window class


## Other TODO

* [ ] Configurable controls
* [ ] Save / Load
* [ ] Network
* [ ] GUI
