import argparse
import requests
import tarfile
import os
import re
from osgeo import gdal, osr
import numpy as np
import tempfile


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


def create_url(lat, lon):
    latstr, lonstr = numerical_coordinates_to_string(lat, lon)
    return f"https://prism-dem-open.copernicus.eu/pd-desk-open-access/prismDownload/COP-DEM_GLO-30-DTED__2023_1/Copernicus_DSM_10_{latstr}_00_{lonstr}_00.tar"


def download_files(lats, lons, download_dir):
    for lat in lats:
        for lon in lons:
            url = create_url(lat, lon)
            print(f"Downloading {url}")
            r = requests.get(url, allow_redirects=True)
            if r.status_code == 200:
                open(f"{download_dir}/{lat}_{lon}.tar", "wb").write(r.content)
            print(f"Downloaded {url}")


def dt2_files(members):
    for tarinfo in members:
        if os.path.splitext(tarinfo.name)[1] == ".dt2":
            tarinfo.name = os.path.basename(tarinfo.name)
            return tarinfo


def create_sea_tile(lat, lon, download_dir):
    # Define the size of the raster (1 degree by 1 degree)
    width = int(3600)  # 1 degree = 3600 arc-seconds at 1" resolution
    height = int(3600)

    # Create a 2D array filled with zeros
    data = np.zeros((height, width), dtype=np.int16)

    # Define the geotransform (top-left x, pixel width, rotation, top-left y, rotation, pixel height)
    geotransform = (lon, 1 / 3600, 0, lat + 1.0, 0, -1 / 3600)

    latstr, lonstr = numerical_coordinates_to_string(lat, lon)
    # Create the dataset
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(
        f"{download_dir}/Copernicus_DSM_10_{latstr}_00_{lonstr}_00_DEM.dt2", width, height, 1, gdal.GDT_Int16
    )

    # Set the geotransform and projection
    dataset.SetGeoTransform(geotransform)

    # Define a simple WGS84 spatial reference system (EPSG:4326)
    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS("WGS84")
    dataset.SetProjection(srs.ExportToWkt())

    # Write the data (band 1)
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)

    # Flush data to disk
    band.FlushCache()

    # Close the dataset
    dataset = None
    return f"Copernicus_DSM_10_{latstr}_00_{lonstr}_00_DEM.dt2"


def extract_dt2(lat, lon, download_dir):
    if not os.path.exists(f"{download_dir}/{lat}_{lon}.tar"):
        return create_sea_tile(lat, lon, download_dir)
    tar = tarfile.open(f"{download_dir}/{lat}_{lon}.tar")
    dt2 = dt2_files(tar.getmembers())
    if dt2 is not None:
        tar.extract(dt2, path=download_dir)
    tar.close()
    return dt2.name if dt2 else None


def extract_coordinates(filename):
    if filename is None:
        return None
    match = re.search(r"[NS]\d{2}_\d{2}_[EW]\d{3}_\d{2}", filename)
    if match:
        return match.group()
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("min_lat", type=int)
    parser.add_argument("max_lat", type=int)
    parser.add_argument("min_lon", type=int)
    parser.add_argument("max_lon", type=int)
    args = parser.parse_args()
    lats = range(args.min_lat, args.max_lat + 1)
    lons = range(args.min_lon, args.max_lon + 1)
    with tempfile.TemporaryDirectory() as temp_dir:
        download_files(lats, lons, temp_dir)
        files = []
        for lat in lats:
            for lon in lons:
                files.append(extract_dt2(lat, lon, temp_dir))

        for file in files:
            if file is None:
                continue
            out_name = f"{extract_coordinates(file)}.tif"
            gdal.Translate(
                out_name,
                f"{temp_dir}/{file}",
                format="GTiff",
                creationOptions=["COMPRESS=LZW", "PREDICTOR=2", "ZLEVEL=9"],
            )
