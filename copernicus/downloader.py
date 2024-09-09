import argparse
import requests
import tarfile
import os
import re
from osgeo import gdal
import tempfile


def create_url(lat, lon):
    if lat < 0:
        latstr = f"S{abs(lat):02d}"
    else:
        latstr = f"N{(lat):02d}"
    if lon < 0:
        lonstr = f"W{(abs(lon)):03d}"
    else:
        lonstr = f"E{(lon):03d}"
    return f"https://prism-dem-open.copernicus.eu/pd-desk-open-access/prismDownload/COP-DEM_GLO-30-DTED__2023_1/Copernicus_DSM_10_{latstr}_00_{lonstr}_00.tar"


def download_files(lats, lons, download_dir):
    for lat in lats:
        for lon in lons:
            url = create_url(lat, lon)
            print(f"Downloading {url}")
            r = requests.get(url, allow_redirects=True)
            open(f"{download_dir}/{lat}_{lon}.tar", "wb").write(r.content)
            print(f"Downloaded {url}")


def dt2_files(members):
    for tarinfo in members:
        if os.path.splitext(tarinfo.name)[1] == ".dt2":
            tarinfo.name = os.path.basename(tarinfo.name)
            return tarinfo


def extract_dt2(lat, lon, download_dir):
    tar = tarfile.open(f"{download_dir}/{lat}_{lon}.tar")
    dt2 = dt2_files(tar.getmembers())
    if dt2 is not None:
        tar.extract(dt2, path=download_dir)
    tar.close()
    return dt2.name if dt2 else None


def extract_coordinates(filename):
    match = re.search(r"N\d{2}_\d{2}_E\d{3}_\d{2}", filename)
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
            out_name = f"{extract_coordinates(file)}.tif"
            gdal.Translate(
                out_name,
                f"{temp_dir}/{file}",
                format="GTiff",
                creationOptions=["COMPRESS=LZW", "PREDICTOR=2", "ZLEVEL=9"],
            )
