import numpy as np


def get_mid_coord(x1, y1, x2, y2):
    a = np.array((x1, y1))
    b = np.array((x2, y2))
    return tuple((a + b) / 2)


def lerp(start, end, t, gs) -> float:
    """Linearly interpolate between start and end by t."""
    return start + (end - start) * t * gs


def ease_in_out_sine(t):
    return -(np.cos(np.pi * np.array(t)) - 1) / 2


def ease_in_out_quad(t: float) -> float:
    """
    Quadratic ease-in-out curve

    Parameters
    ----------
    t : float
        Input value between 0.0 and 1.0

    Returns
    -------
    float
        Output value between 0.0 and 1.0
    """
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t

def ease_in_out_cubic(t: float) -> float:
    t *= 2
    if t < 1:
        return t * t * t / 2
    else:
        t -= 2
        return (t * t * t + 2) / 2


def ease(t: float) -> float:
    return ease_in_out_sine(t)
