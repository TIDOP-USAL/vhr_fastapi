import nest_asyncio
import planet
from utils import (get_auth, create_filters, create_request, create_and_download, query_data)
from basemodels import ItemDict
from typing import Dict, List
import datetime

nest_asyncio.apply()

async def query_datalist(
    api_key: str,
    geometry_json: str,
    item_type: str,
    start_date: str,
    end_date: str,
    cloud_cover: float,
    asset: str,
) -> Dict[str, ItemDict]:
    '''
    Query Planet imagery with the Planet API.
    
    Args:
    - api_key (str): The Planet API key.
    - geometry_json (str): The path to the geojson file.
    - item_type (str): The item type to search for. Options are 'PSScene', 'PSOrthoTile',
      'REOrthoTile', 'SkySatScene', and 'Landsat8L1G', etc.
    - start_date (str): The start date for the search.
    - end_date (str): The end date for the search.
    - cloud_cover (float): The maximum cloud cover percentage.
    - asset (str): The asset to use.

    Returns:
    - Dict[str, ItemDict]: The dict of dict items that match the filters.
    '''

    # Authenticate with the Planet API
    auth = get_auth(api_key)

    # Create the filters
    sfilter = create_filters(geometry_json, start_date, end_date, 
                             cloud_cover, "AndFilter")
    
    # Get the items that match the filters
    items_dicts = await query_data(auth, item_type, sfilter, asset)
    
    return items_dicts


async def create_download(
    api_key: str,
    item_type: str,
    item_lists: List[str],
    geometry_json: str,
    order_name: str,
    product_bundle: str = "analytic_sr_udm2",
) -> None:
    '''
    Create and download an order with the Planet API.

    Args:
    - item_type (str): The item type.
    - item_lists (List[str]): Get the ID lists
    - geometry_json (str): The path to the geojson file.
    - order_name (str): The order name.
    - product_bundle (str): The product bundle.
    - directory (str): The directory to save the order.
    '''

    #Authenticate with the Planet API
    auth = get_auth(api_key)

    # Create the order request
    async with planet.Session(auth=auth) as sess:
        client_order = sess.client("orders")

        # create random order name with hour, minute, and second
        order_name = f"{order_name}_" + datetime.datetime.now().strftime(("%Y-%m-%d_%H-%M-%S"))
        request = create_request(
            item_type,
            item_lists,
            geometry_json,
            order_name,
            product_bundle,
        )

        # Create a folder in your download machine
        output_folder = f"{order_name}"
        # Create and download the order
        await create_and_download(client_order, request, output_folder)
        print(f"Order {order_name} has been created and downloaded.")
