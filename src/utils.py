import json
import numpy as np
import pathlib
import planet
import pyproj
import rasterio as rio

from typing import Dict, List
from basemodels import SFilterDict, ItemDict, OrderDict


def create_geometry(point: List[float], edge_size:int, resolution: int=3) -> str:
    '''
    Create a GeoJSON string for a square geometry centered at the given point.

    Args:
    - point (List[float]): The point coordinates.
    - edge_size (int): The size of the square edge.
    - resolution (int): The resolution of the PlanetScope data.

    Returns:
    - str: The GeoJSON string.
    '''
    # Obtain a element for a list of coordinates
    lon, lat = point

    # Calculate the square buffer
    buffer = (edge_size * resolution / 2) 

    E = lon + buffer
    W = lon - buffer
    N = lat + buffer
    S = lat - buffer

    # Create the square coordinates
    square = [ 
               [W, S],
               [E, S],
               [E, N],
               [W, N],
               [W, S] 
            ]
    
    # Convert to EPSG:4326
    transformer = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    geo_square = [list(transformer.transform(x[0],x[1])) for x in square]

    return geo_square


# Get and store credentials in an Auth object
def get_auth(api_key: str) -> planet.Auth:
    """
    Get the user account from the API key, and store credentials in an Auth object.
    """

    # Store the credentials in an Auth object
    auth = planet.Auth.from_key(api_key)
    auth.store()

    print("Credentials stored in Auth object.")
    return auth


# Create filters for the Planet API request
def create_filters(
    geometry: str,
    edge_size: int,
    start_date: str="2021-01-01T00:00:00Z",
    end_date: str="2021-12-31T23:59:59Z",
    cloud_cover: float=0.5
) -> SFilterDict:
    """
    Create filters for the Planet API request.

    Args:
    - geometry (str): The geometry in string format.
    - edge_size (int): The size of the square edge.
    - date_range (Tuple[str, str]): The date range.
    - cloud_cover (float): The cloud cover percentage to filter if less
      than or equal to. The range is from 0 to 1.

    Returns:
    - SFilterDict: The filters for the Planet API request.
    """
    # Get geometries from a point
    geometry = create_geometry(geometry, edge_size)

    # For geometry
    geometry_filter = {
        "type": "GeometryFilter",
        "field_name": "geometry",
        "config": {"type": "Polygon", 
                   "coordinates": [geometry]}
    }

    # For date range
    date_range_filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {"gte": f"{start_date}T00:00:00Z", 
                   "lte": f"{end_date}T00:00:00Z"
                  }
    }

    # For metadata filter
    cloud_cover_filter = {
        "type": "RangeFilter",
        "field_name": "cloud_cover",
        "config": {"lte": cloud_cover}
    }

    # Stats API request object
    sfilter = {
        "type": "AndFilter",
        "config": [
            geometry_filter, 
            date_range_filter, 
            cloud_cover_filter
        ]
    }

    return sfilter


async def query_data(
    auth: planet.Auth,
    item_type: str,
    sfilter: SFilterDict,
    asset: str = "ortho_analytic_4b_sr",
) -> Dict[str,ItemDict]:
    """
    Query the Planet API for data items id and thumbnails that match 
    the filters.

    Args:
    - auth (planet.Auth): The user account credentials.
    - item_type (str): The item type.
    - sfilter (SFilterDict): The filters for the API request.
    - asset (str): The asset to download.

    Returns:
    - List[ItemDict]: The list of items dictionaries that match the filters.
    """

    # Open a session client for data with the API
    async with planet.Session(auth=auth) as sess:
        client = sess.client("data")

        try:
            counter = 1
            items_dicts = {}
            async for query in client.search([item_type], sfilter):
                if asset in query["assets"]:
                    items_dicts[f"Item_{counter}"] = query
                    counter += 1

            return items_dicts

        except Exception as e:
            print(f"An error occurred: {e}")


# Create a request
def create_request(
    item_type: str,
    item_list: List[str],
    geometry: str,
    edge_size: int,
    product_bundle: str = "analytic_sr_udm2",
) -> OrderDict:
    """
    Create an order request for the Planet API.

    Args:
    - item_type (str): The item type.
    - item_lists (List[str]): Get the ID lists
    - geometry (str): The geometry in string format.
    - edge_size (int): The size of the square edge.
    - product_bundle (str): The product bundle to order.

    Returns:
    - OrderDict: The order request.
    """
    # Get geometries from a point
    geometry = create_geometry(geometry, edge_size)
    # Create order request
    order = planet.order_request.build_request(
        products=[
            planet.order_request.product(
                item_ids=item_list,
                product_bundle=product_bundle,
                item_type=item_type,
            )
        ],
        tools=[
            planet.order_request.clip_tool(aoi={"type": "Polygon", 
                                                "coordinates": [json.loads(geometry)]}),            
            planet.order_request.composite_tool(),
            planet.order_request.harmonize_tool("Sentinel-2")
        ],
    )

    return order


# Create and download the order request
async def create_and_download(
    client: planet.Session.client,
    order_detail: OrderDict,
    directory: str
) -> None:
    """
    Create an order and download the files.

    Args:
    - client (planet.Session.client): The client order object.
    - order_detail (OrderDict): The order request.
    - directory (str): The directory to save the downloaded files.
    """

    # Check the order status
    with planet.reporting.StateBar(state="creating") as bar:
        detail = await client.create_order(order_detail)
        bar.update(state="created", order_id=detail["id"])
        await client.wait(detail["id"], callback=bar.update_state)

    await client.download_order(detail["id"], directory, progress_bar=True)

    ## Return the order id
    return detail["id"]

## Create a folder root and create the structured folders
def create_folder_and_txt(root: str, image_folder: pathlib.Path) -> str:
    """
    Create a folder root and create the structured folders.

    Args:
    - root (str): The root directory.
    - image_folder (pathlib.Path): The image folder.

    Returns:
    - str: The directory path.
    """

    # Create the root folder
    root = pathlib.Path(root)
    root.mkdir(parents=True, exist_ok=True)

    # Get the date for specific file
    manifest = image_folder / "manifest.json"

    with open(manifest, "r") as file:
        data = json.load(file)

    date = data["files"][0]["path"][0]

    # Create the folder
    root_folder = root / f"{date[:3]}_{date[3:5]}_{date[5:7]}"
    root_folder.mkdir(parents=True, exist_ok=True)

    # Create the following subfolders: input, label, and output
    input_folder = root_folder / "input"
    input_folder.mkdir(parents=True, exist_ok=True)

    label_folder = root_folder / "label"
    label_folder.mkdir(parents=True, exist_ok=True)

    for day in ["01", "05", "10", "15", "20", "25"]:

        with rio.open(image_folder / "composite_udm2.tif") as src:
            # Get array
            image = src.read()
            profile = src.profile            
            _, h, w = image.shape

            # Save input images
            with rio.open(input_folder / f"{date[:3]}_{date[3:5]}_{day}.tif", 
                        "w", **src.profile) as dst:
                dst.write(image)
            
            # Generate label image
            label_image = np.zeros((h, w), dtype=np.uint8)
            
            # Profile for label with 1 band
            profile_label = profile.copy()
            profile_label.update(dtype=rio.uint8, count=1)

            # Save label image
            with rio.open(label_folder / f"label_{date[:3]}_{date[3:5]}_{day}.tif", 
                        "w", **profile_label) as dst2:
                dst2.write(label_image)

    # Create the data txt
    with open(root_folder / "test.txt", "w") as file:
        file.write(f"/input /label/{date[:3]}-{date[3:5]}-01.tif {date[:3]}-{date[3:5]}")
        file.write(f"/input /label/{date[:3]}-{date[3:5]}-05.tif {date[:3]}-{date[3:5]}")
        file.write(f"/input /label/{date[:3]}-{date[3:5]}-10.tif {date[:3]}-{date[3:5]}")
        file.write(f"/input /label/{date[:3]}-{date[3:5]}-15.tif {date[:3]}-{date[3:5]}")
        file.write(f"/input /label/{date[:3]}-{date[3:5]}-20.tif {date[:3]}-{date[3:5]}")
        file.write(f"/input /label/{date[:3]}-{date[3:5]}-25.tif {date[:3]}-{date[3:5]}")

    print(f"Folders {root_folder} created successfully.")
    return root_folder