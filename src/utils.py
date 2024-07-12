import asyncio
import json
import pathlib
import planet


from typing import Dict, List, Union
from src.basemodels import SFilterDict, ItemDict, OrderDict

def identify_geometry(coordinates) -> str:
        '''
        Identify the geometry type from the coordinates.

        Args:
        - coordinates (str): The coordinates in JSON format.

        Returns:
        - str: The geometry type.
        '''

        # Convertir la cadena JSON a un objeto Python
        coords = json.loads(coordinates)
        
        # Verify if it is a point
        if isinstance(coords, list) and len(coords) == 2 and all(isinstance(coord, 
                     (float, int)) for coord in coords):
            return "Point"
        
        # Verify if it is a line or polygon
        if isinstance(coords, list) and all(isinstance(coord, list) for coord in coords):
            if len(coords) == 2 and all(len(coord) == 2 for coord in coords):
                return "LineString"
            
            # Verificar si es un polígono
            if all(len(coord) == 2 for coord in coords[0]):
                if len(coords[0]) >= 3 and coords[0][0] == coords[0][-1]:
                    return "Polygon"
        return "Unknown"

    
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
    geometry_json: str,
    start_date: str="2021-01-01T00:00:00Z",
    end_date: str="2021-12-31T23:59:59Z",
    cloud_cover: float=0.5,
    logical_filter: str = "AndFilter",
) -> SFilterDict:
    """
    Create filters for the Planet API request.

    Args:
    - geometry_json (str): The path to the geojson file.
    - date_range (Tuple[str, str]): The date range.
    - cloud_cover (float): The cloud cover percentage to filter if less
      than or equal to. The range is from 0 to 1.
    - logical_filter (str): The logical filter to use. Options are 'AndFilter'
      and 'OrFilter'.

    Returns:
    - SFilterDict: The filters for the Planet API request.
    """
        
    # For geometry
    geometry_filter = {
        "type": "GeometryFilter",
        "field_name": "geometry",
        "config": {"type": f"{identify_geometry(geometry_json)}", 
                   "coordinates": json.loads(geometry_json)}
    }

    # For date range
    date_range_filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {"gte": start_date, "lte": end_date},
    }

    # For metadata filter
    cloud_cover_filter = {
        "type": "RangeFilter",
        "field_name": "cloud_cover",
        "config": {"lte": cloud_cover},
    }

    # Stats API request object
    sfilter = {
        "type": logical_filter,
        "config": [
            geometry_filter, 
            date_range_filter, 
            cloud_cover_filter
        ]
    }

    return sfilter


async def query_data(
    auth: planet.Auth,
    item_type: Union[str, List[str]],
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
    item_lists: List[str],
    geometry_json: str,
    order_name: str,
    product_bundle: str = "analytic_sr_udm2",
) -> OrderDict:
    """
    Create an order request for the Planet API.

    Args:
    - item_type (str): The item type.
    - item_lists (List[str]): The list of item ids.
    - geometry_json (str): The path to the geojson file.
    - order_name (str): The name of the order request.
    - product_bundle (str): The product bundle to order.

    Returns:
    - OrderDict: The order request.
    """

    # Get the item ids
    item_ids = [item["id"] for item in item_lists]

    # Create order request
    order = planet.order_request.build_request(
        name=order_name,
        products=[
            planet.order_request.product(
                item_ids=item_ids,
                product_bundle=product_bundle,
                item_type=item_type,
            )
        ],
        tools=[
            planet.order_request.clip_tool(aoi=geometry_json),            
            planet.order_request.composite_tool(),
            planet.order_request.harmonize_tool("Sentinel-2")
        ],
    )

    return order


# Create and download the order request
async def create_and_download(
    client: planet.Session.client,
    order_detail: OrderDict,
    directory: str = "downloads",
) -> None:
    """
    Create an order and download the files.

    Args:
    - client (planet.Session.client): The client order object.
    - order_detail (OrderDict): The order request.
    - directory (str): The directory to save the downloaded files.
    """

    # Create a directory to store the downloaded files
    directory = pathlib.Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    # Check the order status
    with planet.reporting.StateBar(state="creating") as bar:
        detail = await client.create_order(order_detail)
        bar.update(state="created", order_id=detail["id"])
        await client.wait(detail["id"], callback=bar.update_state)

    await client.download_order(detail["id"], directory, progress_bar=True)
