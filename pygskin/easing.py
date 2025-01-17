"""Easing functions."""

import math


def sine_in(x: float) -> float:
    return 1 - math.cos((x * math.pi) / 2)


def sine_out(x: float) -> float:
    return math.sin((x * math.pi) / 2)


def sine_in_out(x: float) -> float:
    return -(math.cos(math.pi * x) - 1) / 2


def cubic_in(x: float) -> float:
    return x**3


def cubic_out(x: float) -> float:
    return 1 - (1 - x) ** 3


def cubic_in_out(x: float) -> float:
    return 4 * x**3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def expo_in(x: float) -> float:
    return 0 if x == 0 else 2 ** (10 * x - 10)


def expo_out(x: float) -> float:
    return 1 if x == 1 else 1 - 2 ** (-10 * x)


def expo_in_out(x: float) -> float:
    if x in {0, 1}:
        return x
    return 2 ** (20 * x - 10) / 2 if x < 0.5 else (2 - 2 ** (-20 * x + 10)) / 2


def bounce_in(x: float) -> float:
    return 1 - bounce_out(1 - x)


def bounce_out(x: float) -> float:
    n1 = 7.5625
    d1 = 2.75
    if x < 1 / d1:
        return n1 * x**2
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x**2 + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x**2 + 0.9375
    x -= 2.625 / d1
    return n1 * x**2 + 0.984375


def bounce_in_out(x: float) -> float:
    if x < 0.5:
        return (1 - bounce_out(1 - 2 * x)) / 2
    return (1 + bounce_out(2 * x - 1)) / 2
