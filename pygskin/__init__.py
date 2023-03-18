import sys

from pygskin.assets import Image
from pygskin.assets import Music
from pygskin.assets import Sound
from pygskin.dialogue import Dialogue
from pygskin.direction import Direction
from pygskin.events import Event
from pygskin.input import Input
from pygskin.input import InputHandler
from pygskin.interfaces import Drawable
from pygskin.interfaces import Updatable
from pygskin.pubsub import message
from pygskin.spritesheet import CachedSpritesheet
from pygskin.spritesheet import Spritesheet
from pygskin.state_machine import StateMachine
from pygskin.text import Text
from pygskin.timer import Timer
from pygskin.window import Window

for class_ in Event.CLASSES.values():
    setattr(sys.modules[__name__], class_.__name__, class_)

__all__ = [
    "Image",
    "Music",
    "Sound",
    "Dialogue",
    "Direction",
    "Event",
    "Input",
    "InputHandler",
    "Drawable",
    "Updatable",
    "message",
    "CachedSpritesheet",
    "Spritesheet",
    "StateMachine",
    "Text",
    "Timer",
    "Window",
    *[class_.__name__ for class_ in Event.CLASSES.values()],
]
