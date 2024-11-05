## Download images using cubo
import rasterio as rio
import rioxarray
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import pathlib
import pystac_client
import planetary_computer as pc
import stackstac
from typing import List, Union

import shapely.geometry
from pyproj import Transformer
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info

def create(
    lat: Union[float, int],
    lon: Union[float, int],
    collection: str,
    bands: List[str],
    name_id: int,
    start_date: str,
    end_date: str,
    edge_size: Union[float, int],
    resolution: Union[float, int],
    out_folder: str,
    stac: str= "https://planetarycomputer.microsoft.com/api/stac/v1",
    **kwargs
) -> None:
    """Creates a Bounding Box (BBox) given a pair of coordinates and a buffer distance.
    Parameters
    ----------
    lat : float
        Latitude.
    lon : float
        Longitude.
    collection : str
        Name of the collection in the STAC catalogue.
    bands : List[str]
         Name of the band(s) from the collection to use. 
    name_id : int
        Identifier of the point.
    start_date : str
        Start date of the data cube in the "YYYY-MM-DD" format .
    end_date : str
        End date of the data cube in the "YYYY-MM-DD" format .
    edge_size : float
        Buffer distance in meters.
    resolution : int | float
        Spatial resolution to use.
    out_folder : str
        Path to the folder where the first image will be saved. Within this folder, 
        it will be created three subfolders: "input", "output", and "geojson". The 
        last one will contain the bbox_utm in GeoJSON format.
    stac : str
        URL of the STAC catalogue in Planetary Computer.
    Returns
    -------
    tuple
        BBox in UTM coordinates, BBox in latlon, and EPSG.
    """
    # Get the UTM EPSG from latlon
    utm_crs_list = query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(lon, lat, lon, lat),
    )

    # Save the CRS
    epsg = utm_crs_list[0].code

    # Initialize a transformer to UTM
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)

    # Initialize a transformer from UTM to latlon
    inverse_transformer = Transformer.from_crs(
        f"EPSG:{epsg}", "EPSG:4326", always_xy=True
    )

    # Transform latlon to UTM
    utm_coords = transformer.transform(lon, lat)

    # Round the coordinates
    utm_coords_round = [round(coord / resolution) * resolution for coord in utm_coords]

    # Buffer size
    buffer = round(edge_size * resolution / 2)

    # Create BBox coordinates according to the edge size
    E = utm_coords_round[0] + buffer # maxx
    W = utm_coords_round[0] - buffer # minx
    N = utm_coords_round[1] + buffer # maxy
    S = utm_coords_round[1] - buffer # miny

    # Create polygon from BBox coordinates
    polygon = [
        [W, S],
        [E, S],
        [E, N],
        [W, N],
        [W, S],
    ]

    # Transform vertices of polygon to latlon
    polygon_latlon = [list(inverse_transformer.transform(x[0], x[1])) for x in polygon]

    ## Convert UTM Bbox to a Feature
    bbox_utm_bounds = shapely.geometry.box(W, S, E, N)

    # Create latlon BBox
    bbox_latlon = {
        "type": "Polygon",
        "coordinates": [polygon_latlon],
    }

    # Open the Catalogue
    CATALOG = pystac_client.Client.open(stac)

    # Do a search
    SEARCH = CATALOG.search(
        intersects=bbox_latlon,
        datetime=f"{start_date}/{end_date}",
        collections=[collection],
        **kwargs
    )
    
    # Get all items and sign if using Planetary Computer
    items = SEARCH.item_collection()
    
    items = pc.sign(items)

    # Add stackstac arguments
    stackstac_kw = dict()

     # Create the cube
    cube = stackstac.stack(
        items,
        assets=bands,
        resolution=resolution,
        bounds=bbox_utm_bounds.bounds,
        xy_coords="topleft",
        epsg=int(epsg),
        **stackstac_kw,
    )

    # Delete attributes
    attributes = ["spec", "crs", "transform", "resolution"]

    for attribute in attributes:
        if attribute in cube.attrs:
            del cube.attrs[attribute]

    # Rounded edge size
    rounded_edge_size = cube.x.shape[0]

    # New attributes
    cube.attrs = dict(
        collection=collection,
        stac=stac,
        epsg=int(epsg),
        resolution=resolution,
        edge_size=rounded_edge_size,
        edge_size_m=rounded_edge_size * resolution,
        central_lat=lat,
        central_lon=lon,
        central_y=utm_coords[1],
        central_x=utm_coords[0],
        time_coverage_start=start_date,
        time_coverage_end=end_date,
    )
    # New name
    cube.name = collection

    ## Save cube as a geotiff
    ## Get crs and transform
    transform = cube.rio.transform()
    crs = f"EPSG:{epsg}"
    cube.rio.write_crs(crs, inplace=True)
    cube.rio.write_transform(transform, inplace=True)

    ## Create subfolders
    out_folder = pathlib.Path(out_folder) 
    out_folder.mkdir(parents=True, exist_ok=True)

    ## Save as a geotiff
    nstr = str(name_id).zfill(5)

    for folder in ["input", "output", "geojson"]:
        (out_folder / folder).mkdir(exist_ok=True) 
    
    ## Generate a geojson from cub    
    cube_bounds = cube.rio.bounds()
    ## Convert to a shapely geometry
    cube_bounds = shapely.geometry.box(*cube_bounds)
    ## Convert a geodatframe using shapely
    bbox_utm_gdf = gpd.GeoDataFrame(geometry=[cube_bounds], crs=crs)
    bbox_utm_gdf.to_file(f"{out_folder}/geojson/bbox_{nstr}.geojson", driver="GeoJSON")
    
    ## Save the first image as a geotiff
    cube.isel(time=0).rio.to_raster(f"{out_folder}/input/image_{nstr}.tif")

    print(f"Cube saved in {out_folder}")

# grep -e "^ESP" Europe-Full.tsv | cut -c5- > Spain_roads.parquet  
## Get the roads inside the Spain filtered area
roads = gpd.read_parquet("Spain_roads.parquet")

centroids = gpd.read_file("Spain_centroids.geojson")
centroids["id"] = centroids.index

for n in range(len(centroids)):
    point = centroids.geometry[n]
    lat, lon = point.y, point.x
    try:
        create(
            lat=lat, # Central latitude of the cube
            lon=lon, # Central longitude of the cube
            collection="sentinel-2-l2a", # Name of the STAC collection
            bands=["B04","B03","B02", "B08"], # Bands to retrieve
            name_id=n,
            start_date="2022-06-01", # Start date of the cube
            end_date="2022-07-01", # End date of the cube
            edge_size=128, # Edge size of the cube (px)
            resolution=10, # Pixel size of the cube (m)
            out_folder="/media/tidop/Datos_4TB/databases/sr_seg",
            query={"eo:cloud_cover": {"lt": 10}}, # Query for the EO data
        )
        print(f"[{n+1}/{len(centroids)}] Cube created for point {n}")
    except Exception as e:
        print(f"[{n+1}/{len(centroids)}] Error in point {n}: {e}")
        continue

## For each tile in the grid, binarize the buildings

def binarize_images(aoi_path: str,
                    database_type: str,
                    reference_image_path: str,
                    output_path:str
) -> None:
    """
    Binarize the buildings or roads from vector data in a specific area of interest (AOI).
    Args:
    aoi_path_list: List[str]
        Path to the area of interest (AOI) in GeoJSON format.
    database_type: str
        Type of the database to use. It can be either "buildings" or "roads".
    reference_image_path_list: List[str]
        Path to the reference image in GeoTIFF format.
    output_path: str
        Path to the output folder where the binarized images will be saved.
    """
    ## Open the large database
    if database_type == "buildings":
        database_path = "Spain_buildings.parquet"
        database = gpd.read_parquet(database_path)
    elif database_type == "roads":
        database_path = "Spain_roads.geojson"
        database = gpd.read_file(database_path)    
    print("Database loaded correctly") 

    ## Get the list of AOI
    aoi_path_list = sorted(list(pathlib.Path(aoi_path).glob("*.geojson")))
    
    for i, file in enumerate(aoi_path_list):
        ## Filename without extension
        filename = file.stem
        nstr = filename.split("_")[-1]

        ## Get the reference image in input folder
        image_folder = file.parent.parent / "input"
        reference_image_path = image_folder / f"image_{nstr}.tif"

        if reference_image_path.exists():
            with rio.open(reference_image_path) as src:
                img_transform = src.transform
                img_profile = src.profile 
                crs = src.crs.to_epsg()  

                ## Open AOI as a geodataframe
                aoi = gpd.read_file(file)

                ## Convert to the same crs as the reference image
                aoi = aoi.to_crs(epsg=crs)                
                database = database.to_crs(epsg=crs)
                
                ## Filter the database by the AOI               
                vector = database[database.geometry.within(aoi.geometry[0])]
                
                ## Generate a buffer of 5 meters each side
                vector.geometry = vector.buffer(5)

                # Calculate the scale factor
                new_width = int(src.width * 4)
                new_height = int(src.height * 4)

                # Generate a binary image with the new dimensions
                img = np.zeros((new_height, new_width), dtype=np.uint8)

                # Create a new transform based on the desired resolution
                bin_transform = rio.Affine(
                    2.5, img_transform.b, img_transform.c,
                    img_transform.d, -2.5, img_transform.f
                )

                geometries = [(geom, 1) for geom in vector.geometry]

                img = rio.features.rasterize(
                    geometries,
                    out_shape=(new_height, new_width),
                    transform=bin_transform,
                    fill=0,
                    all_touched=True,
                    dtype="uint8"
                )

                ## Save the binary image
                img = (img > 0).astype("uint8")

                ## Save the binary image
                output_path  = pathlib.Path(output_path)
                type_path = (output_path / database_type)
                type_path.mkdir(parents=True, exist_ok=True)

                ## Update the profile
                bin_profile = img_profile.copy()
                bin_profile.update(
                    dtype="uint8",
                    height=new_height,
                    width=new_width,
                    count=1,
                    compress="lzw",
                    transform=bin_transform
                )

                with rio.open(type_path / f"{database_type}_{nstr}.tif", "w", **bin_profile) as dst:
                    dst.write(img, 1)
                
                print(f"[{i+1}/{len(aoi_path_list)}] Binary image saved in {type_path}")
        else:
            print(f"[{i+1}/{len(aoi_path_list)}] Reference image not found for {nstr}")
            continue


## Apply the function for buildings
binarize_images( aoi_path="/media/tidop/Datos_4TB/databases/sr_seg/geojson",
                 database_type="buildings",
                 reference_image_path="/media/tidop/Datos_4TB/databases/sr_seg/input",
                 output_path="/media/tidop/Datos_4TB/databases/sr_seg"
)


## Apply the function for roads
binarize_images( aoi_path="/media/tidop/Datos_4TB/databases/sr_seg/geojson",
                 database_type="roads",
                 reference_image_path="/media/tidop/Datos_4TB/databases/sr_seg/input",
                 output_path="/media/tidop/Datos_4TB/databases/sr_seg"
)   