import math


def circle_path(quotient: float, radius: float, offset: float) -> tuple[float, float]:
    angle = 2 * math.pi * quotient + 2 * math.pi * offset
    return math.cos(angle) * radius, math.sin(angle) * radius

