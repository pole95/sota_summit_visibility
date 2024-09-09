# SOTA Summits LoS
[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

A script to determine which SOTA summits are within line of sight of eachother.

To determine the elevation, it uses elevation data from the [Copernicus](https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model) program from ESA.

## Setup

Run `download_summits.py` first to generate the database of all SOTA summits.

## Usage
``` bash
python generate_los_list.py  [--max_distance MAX_DISTANCE] [--tx_height TX_HEIGHT] [--rx_height RX_HEIGHT] [--output OUTPUT] SummitCode
```
`SummitCode`: complete summit code for the main summit, including association (e.g. **HB/ZH-004**)

`MAX_DISTANCE`: maximum distance up to which summits are considered in km, default 100km

`TX_HEIGHT`: height of the transmitting antenna, default 2m

`RX_HEIGHT`: height of the receiving antenna, default 2m

`OUTPUT`: csv filename, default "output.csv"

## Requirements

GDAL, geopy, numpy, rasterio, shapely

---


This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
