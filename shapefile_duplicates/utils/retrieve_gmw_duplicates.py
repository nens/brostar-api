import datetime
import logging

import geopandas as gpd

from .duplicates_handler import GMWDuplicatesHandler
from .ogc_reader import DataRetrieverOGC

logger = logging.getLogger(__name__)


def get_bbox_from_shapefile(shapefile):
    if shapefile is None:
        raise ValueError("Shapefile is required to get the bounding box.")

    # Load the shapefile
    if shapefile.endswith(".zip"):
        gdf = gpd.read_file(
            f"zip://{shapefile}",
            engine="fiona",
        )
    else:
        gdf = gpd.read_file(shapefile, engine="fiona")

    gdf = gdf.to_crs(epsg=4326)  # Ensure the CRS is WGS84

    # Get the bounding box
    minx, miny, maxx, maxy = gdf.total_bounds
    return (minx, miny, maxx, maxy)


class BBOX:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __init__(self, xmin, ymin, xmax, ymax):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax


def run(kvk_number=None, bro_type: str = "gmw", shapefile=None):
    bbox = get_bbox_from_shapefile(shapefile)
    bbox = BBOX(bbox[0], bbox[1], bbox[2], bbox[3])
    print("bbox settings: ", bbox)
    DR = DataRetrieverOGC(bbox)
    DR.request_bro_ids(bro_type)
    DR.filter_ids_kvk(kvk_number)
    DR.enforce_shapefile(shapefile, delete=False)

    GMWDH = GMWDuplicatesHandler(DR.features)
    GMWDH.get_duplicates(properties=["well_code", "nitg_code"])
    GMWDH.rank_duplicates()
    filename = GMWDH.store_duplicates(
        kvk_number=kvk_number, date=datetime.datetime.now().strftime("%Y%m%d")
    )
    return filename
    # GMWDH.omit_duplicates()
