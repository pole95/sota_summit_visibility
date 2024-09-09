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


def numerical_coordinates_to_string(lat, lon):
    if lat < 0:
        latstr = f"S{abs(lat):02d}"
    else:
        latstr = f"N{(lat):02d}"
    if lon < 0:
        lonstr = f"W{(abs(lon)):03d}"
    else:
        lonstr = f"E{(lon):03d}"
    return latstr, lonstr


def string_coordinates_to_numerical(coordinate_string):
    parts = coordinate_string.split("_")
    lat = int(parts[0][1:])
    if parts[0][0] == "S":
        lat = -lat
    lon = int(parts[2][1:])
    if parts[1][0] == "W":
        lon = -lon
    return lat, lon
