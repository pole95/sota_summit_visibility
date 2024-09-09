import rasterio
import rasterio.merge
import rasterio.transform
from rasterio.io import MemoryFile
import shapely
from math import floor, sqrt, ceil
import numpy as np
import pyproj
import sqlite3
import itertools
import tqdm

db = sqlite3.connect("summits.db")
c = db.cursor()

tf = None
ds = None
loaded_tiles = set()


def get_summit(code):
    return c.execute("SELECT longitude,latitude,elevation FROM summits WHERE SummitCode = ?", (code,)).fetchone()


def extract_profile(ds, tf, line, n_points=512):
    profile = []
    for i in range(n_points):
        p = line.interpolate(i / n_points, normalized=True)
        x, y = rasterio.transform.rowcol(tf, p.x, p.y)
        profile.append(ds[x, y])
    return profile


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


def get_line_distance(line):
    geod = pyproj.Geod(ellps="WGS84")
    start = line.coords[0]
    stop = line.coords[-1]
    _, _, dist = geod.inv(start[0], start[1], stop[0], stop[1])
    return float(dist) if dist else -1  # type: ignore


def apply_earth_curvature(profile, distance):
    corr_profile = profile.copy()
    earth_radius = 6378137
    for i in range(len(profile)):
        curvature = sqrt(earth_radius**2 + distance[i] ** 2) - earth_radius
        corr_profile[i] -= curvature
    return corr_profile


def get_touched_tiles(line, num_points):
    tiles = set()
    for i in range(num_points):
        p = line.interpolate(i / num_points, normalized=True)
        x, y = floor(p.x), floor(p.y)
        tiles.add((x, y))
    return tiles


def get_tile_filename(lon, lat):
    if lat < 0:
        latstr = f"S{abs(lat):02d}"
    else:
        latstr = f"N{(lat):02d}"
    if lon < 0:
        lonstr = f"W{(abs(lon)):03d}"
    else:
        lonstr = f"E{(lon):03d}"
    return f"copernicus/{latstr}_00_{lonstr}_00.tif"


def add_touched_tiles(tileset: set):
    global tf, ds, loaded_tiles
    tilediff = tileset.difference(loaded_tiles)
    if tilediff:
        filenames = [get_tile_filename(x, y) for (x, y) in tilediff]
        datasets = list(map(rasterio.open, filenames))
        if ds is not None and tf is not None:
            memfile = MemoryFile()
            merged_dataset = memfile.open(
                driver="GTiff",
                height=ds.shape[1],  # Height of merged raster
                width=ds.shape[2],  # Width of merged raster
                count=1,  # Number of bands
                dtype=ds.dtype,  # Data type
                crs=datasets[0].crs,  # CRS should match with new tile
                transform=tf,  # Use the transform of the merged raster
            )
            merged_dataset.write(ds[0], 1)  # Write the merged DSM to memory dataset
            all_datasets = [merged_dataset] + datasets
        else:
            all_datasets = datasets
        ds, tf = rasterio.merge.merge(all_datasets)
        loaded_tiles = loaded_tiles.union(tilediff)


def get_profile(point1, point2):
    x1, y1 = point1[0], point1[1]
    x2, y2 = point2[0], point2[1]
    line = shapely.geometry.LineString([(x1, y1), (x2, y2)])
    dist = get_line_distance(line)
    num_points = ceil(dist / 30)
    tiles = get_touched_tiles(line, num_points)
    add_touched_tiles(tiles)
    profile = extract_profile(ds[0, :, :], tf, line, num_points + 1)  # type: ignore
    cum_dist = np.linspace(0, dist, num_points + 1)

    return cum_dist, profile


def linear_interpolate(x1, x2, y1, y2, x):
    return (y1 * (x2 - x) + y2 * (x - x1)) / (x2 - x1)


def can_see(point1, point2):
    cum_dist, profile = get_profile(point1, point2)
    corr_profile = apply_earth_curvature(profile, cum_dist)
    for i in range(len(corr_profile)):
        if (corr_profile[i] - 5) > linear_interpolate(
            0, cum_dist[-1], corr_profile[0] + 2, corr_profile[-1] + 2, cum_dist[i]
        ):
            return False
    return True


summits = {
    code: (lon, lat)
    for code, lon, lat in c.execute(
        """SELECT
    summits.SummitCode, summits.Longitude, summits.Latitude
    FROM
        summits
    INNER JOIN
        regions ON summits.RegionID = regions.RegionID
    INNER JOIN
        associations ON regions.AssociationID = associations.AssociationID
        WHERE
        associations.AssociationName = 'Switzerland'"""
    ).fetchall()
}

with open("viewable_summits.csv", "w") as f:
    f.write("Summit1,Summit2,Viewable\n")
    summit_pairs = itertools.combinations(summits.keys(), 2)
    num_pairs = sum(1 for _ in itertools.combinations(summits.keys(), 2))
    with tqdm.tqdm(total=num_pairs) as pbar:
        for pair in summit_pairs:
            if can_see(summits[pair[0]], summits[pair[1]]):
                # print(f"{pair[0]} and {pair[1]} can see eachother")
                f.write(f"{pair[0]},{pair[1]},true\n")
            else:
                # print(f"{pair[0]} and {pair[1]} CANNOT see eachother")
                f.write(f"{pair[0]},{pair[1]},false\n")
            pbar.update(1)
