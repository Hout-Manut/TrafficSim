import numpy as np


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
