import numpy as np
import matplotlib.pyplot as plt
from math import sqrt

from utils import apply_earth_curvature


def plot_el_prof(profile, cum_dist):
    corr_profile = apply_earth_curvature(profile, cum_dist)
    shift_correction = np.linspace(profile[0] - corr_profile[0], profile[-1] - corr_profile[-1], len(cum_dist))
    corr_profile += shift_correction
    plt.plot(cum_dist, corr_profile)
    plt.plot([0, cum_dist[-1]], [corr_profile[0], corr_profile[-1]])
    plt.savefig("profile.png")


c0 = 299792458


def fresnel_zone(x1, x2, y1, y2, freq):
    lam = c0 / freq
    a = 1 / 2 * sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    r = sqrt(lam * a) / 2
    t = np.linspace(0, 2 * np.pi, 300)
    X = a * np.cos(t)
    Y = r * np.sin(t)
    w = np.arctan2(y2 - y1, x2 - x1)
    x = (x1 + x2) / 2 + X * np.cos(w) - Y * np.sin(w)
    y = (y1 + y2) / 2 + X * np.sin(w) + Y * np.cos(w)
    return x, y
