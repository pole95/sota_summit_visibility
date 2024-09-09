# SOTA summits LoS

This script determines which summits are within line of sight of eachother.

To determine the elevation, it uses elevation data from the [Copernicus](https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model) program from ESA.

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