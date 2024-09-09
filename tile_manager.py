from math import ceil, floor
import numpy as np
import rasterio
import rasterio.merge
from rasterio.io import MemoryFile
import rasterio.transform

from utils import get_line_distance, make_line


class TileManager:
    def __init__(self):
        self.dataset = None
        self.transform = None
        self.loaded_tiles = set()

    def _get_tile_filename(self, lon, lat):
        if lat < 0:
            latstr = f"S{abs(lat):02d}"
        else:
            latstr = f"N{(lat):02d}"
        if lon < 0:
            lonstr = f"W{(abs(lon)):03d}"
        else:
            lonstr = f"E{(lon):03d}"
        return f"copernicus/{latstr}_00_{lonstr}_00.tif"

    def _get_touched_tiles(self, line, num_points):
        tiles = set()
        for i in range(num_points):
            p = line.interpolate(i / num_points, normalized=True)
            x, y = floor(p.x), floor(p.y)
            tiles.add((x, y))
        return tiles

    def _add_touched_tiles(self, line, num_points):
        tileset = self._get_touched_tiles(line, num_points)
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
        profile = []
        for i in range(n_points):
            p = line.interpolate(i / n_points, normalized=True)
            x, y = rasterio.transform.rowcol(self.transform, p.x, p.y)
            profile.append(self.dataset[0, x, y])  # type: ignore
        return profile

    def get_profile(self, point1, point2):
        line = make_line(point1, point2)
        dist = get_line_distance(line)
        num_points = ceil(dist / 30)
        self._add_touched_tiles(line, num_points)
        profile = self._get_dem_profile(line, num_points + 1)  # type: ignore
        cum_dist = np.linspace(0, dist, num_points + 1)

        return cum_dist, profile
