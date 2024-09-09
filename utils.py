from math import sqrt
import pyproj
import shapely


def make_line(point1, point2):
    x1, y1 = point1[0], point1[1]
    x2, y2 = point2[0], point2[1]
    return shapely.geometry.LineString([(x1, y1), (x2, y2)])


def get_distance(point1, point2):
    return get_line_distance(make_line(point1, point2))


def get_line_distance(line):
    geod = pyproj.Geod(ellps="WGS84")
    start = line.coords[0]
    stop = line.coords[-1]
    _, _, dist = geod.inv(start[0], start[1], stop[0], stop[1])
    return float(dist) if dist else -1  # type: ignore


def linear_interpolation(x1, x2, y1, y2, x):
    return (y1 * (x2 - x) + y2 * (x - x1)) / (x2 - x1)


def apply_earth_curvature(profile, distance):
    corr_profile = profile.copy()
    earth_radius = 6378137
    for i in range(len(profile)):
        curvature = sqrt(earth_radius**2 + distance[i] ** 2) - earth_radius
        corr_profile[i] -= curvature
    return corr_profile
