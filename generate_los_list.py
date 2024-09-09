import argparse
from math import floor
import sqlite3
import tqdm
from tile_manager import TileManager
from utils import apply_earth_curvature, linear_interpolation
import geopy
from geopy.distance import geodesic

DEM_RMSE = 5  # [m]


def get_square_corners(lat, lon, radius):
    center = geopy.Point(lat, lon)
    bottom_left = geodesic(kilometers=radius).destination(center, 225)
    top_right = geodesic(kilometers=radius).destination(center, 45)
    return (bottom_left.latitude, bottom_left.longitude, top_right.latitude, top_right.longitude)


db = sqlite3.connect("summits.db")
c = db.cursor()

tf = None
ds = None
loaded_tiles = set()


def get_summit(code):
    return c.execute("SELECT longitude,latitude FROM summits WHERE SummitCode = ?", (code,)).fetchone()


def is_visible(point1, point2, tile_manager, tx_heihgt=2, rx_height=2):
    cum_dist, profile = tile_manager.get_profile(point1, point2)
    corr_profile = apply_earth_curvature(profile, cum_dist)
    for i in range(len(corr_profile)):
        if (corr_profile[i] - DEM_RMSE) > linear_interpolation(
            0, cum_dist[-1], corr_profile[0] + tx_heihgt, corr_profile[-1] + rx_height, cum_dist[i]
        ):
            return False
    return True


def get_summits_distance_from_point(lat, lon, distance):
    lat1, lon1, lat2, lon2 = get_square_corners(lat, lon, distance)
    res = c.execute(
        """
        SELECT SummitCode,longitude,latitude
        FROM summits
        WHERE latitude BETWEEN ? AND ?
        AND longitude BETWEEN ? AND ?""",
        (lat1, lat2, lon1, lon2),
    ).fetchall()
    return {code: (lon, lat) for code, lon, lat in res}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("SummitCode", type=str)
    parser.add_argument("--max-distance", type=int, default=100)
    parser.add_argument("--tx-height", type=int, default=2)
    parser.add_argument("--rx-height", type=int, default=2)
    parser.add_argument("--output", type=str, default="output.csv")
    args = parser.parse_args()
    summit = get_summit(args.SummitCode)
    if summit is None:
        print("Summit not found")
        exit(1)
    tm = TileManager()
    other_summits = get_summits_distance_from_point(summit[1], summit[0], args.max_distance)
    tiles = []
    min_lat, min_lon, max_lat, max_lon = get_square_corners(summit[1], summit[0], args.max_distance)
    for y in range(floor(min_lat), floor(max_lat) + 1):
        for x in range(floor(min_lon), floor(max_lon) + 1):
            tiles.append((x, y))
    tm.load_tiles(tiles)

    output = []
    with tqdm.tqdm(total=len(other_summits)) as pbar:
        for code, point in other_summits.items():
            if code == args.SummitCode:
                continue
            output.append(is_visible(summit, point, tm, args.tx_height, args.rx_height))
            pbar.update(1)
    with open(args.output, "w") as f:
        f.write("SummitCode,Visible\n")
        for code, visible in zip(other_summits.keys(), output):
            f.write(f"{code},{visible}\n")
