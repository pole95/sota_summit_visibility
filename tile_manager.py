from math import ceil
import os
import numpy as np
import rasterio
import rasterio.merge
from rasterio.io import MemoryFile
import rasterio.transform

from downloader import Downloader
from utils import get_line_distance, make_line, numerical_coordinates_to_string


class TileManager:
    def __init__(self):
        self.dataset = None
        self.transform = None
        self.loaded_tiles = set()
        self._downloader = Downloader()

    def _get_tile_filename(self, lon, lat):
        latstr, lonstr = numerical_coordinates_to_string(lat, lon)
        return f"tiles/{latstr}_00_{lonstr}_00.tif"

    def load_tiles(self, tiles):
        missing_tiles = list(filter(lambda t: not os.path.exists(self._get_tile_filename(*t)), tiles))
        print(f"Missing {len(missing_tiles)} tiles")
        if missing_tiles:
            self._downloader.download_tiles(missing_tiles, "tiles")

        filenames = [self._get_tile_filename(x, y) for (x, y) in tiles]
        datasets = list(map(rasterio.open, filenames))
        self.dataset, self.transform = rasterio.merge.merge(datasets)
        self.loaded_tiles = self.loaded_tiles.union(tiles)

    def add_tiles(self, tileset):
        tilediff = tileset.difference(self.loaded_tiles)
        if tilediff:
            filenames = [self._get_tile_filename(x, y) for (x, y) in tilediff]
            datasets = list(map(rasterio.open, filenames))
            if self.dataset is not None and self.transform is not None:
                memfile = MemoryFile()
                merged_dataset = memfile.open(
                    driver="GTiff",
                    height=self.dataset.shape[1],  # Height of merged raster
                    width=self.dataset.shape[2],  # Width of merged raster
                    count=1,  # Number of bands
                    dtype=self.dataset.dtype,  # Data type
                    crs=datasets[0].crs,  # CRS should match with new tile
                    transform=self.transform,  # Use the transform of the merged raster
                )
                merged_dataset.write(self.dataset[0], 1)  # Write the merged DSM to memory dataset
                all_datasets = [merged_dataset] + datasets
            else:
                all_datasets = datasets
            self.dataset, self.transform = rasterio.merge.merge(all_datasets)
            self.loaded_tiles = self.loaded_tiles.union(tilediff)

    def _get_dem_profile(self, line, n_points=512):
        lons = []
        lats = []
        for i in range(n_points):
            p = line.interpolate(i / n_points, normalized=True)
            lons.append(p.x)
            lats.append(p.y)
        xs, ys = rasterio.transform.rowcol(self.transform, lons, lats)
        return self.dataset[0, xs, ys]  # type: ignore

    def get_profile(self, point1, point2):
        line = make_line(point1, point2)
        dist = get_line_distance(line)

        num_points = ceil(dist / 30)
        profile = self._get_dem_profile(line, num_points + 1)  # type: ignore
        cum_dist = np.linspace(0, dist, num_points + 1)

        return cum_dist, profile
