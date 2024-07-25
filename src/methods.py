import nest_asyncio
import planet
from utils import (get_auth, create_filters, create_request, create_and_download, query_data)
from basemodels import ItemDict
from typing import Dict, List
import datetime
import pathlib
import json

nest_asyncio.apply()

async def query_datalist(
    api_key: str,
    geometry: str,
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
    - geometry (str): The geometry in string format.
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
    sfilter = create_filters(geometry, start_date, end_date, 
                             cloud_cover, "AndFilter")
    
    # Get the items that match the filters
    items_dicts = await query_data(auth, item_type, sfilter, asset)
    
    return items_dicts


async def create_download(
    api_key: str,
    item_type: str,
    item_list: str,
    geometry: str,
    order_dir: str,
    product_bundle: str
) -> None:
    '''
    Create and download an order with the Planet API.

    Args:
    - api_key (str): The Planet API key.
    - item_type (str): The item type.
    - item_list (str): Get the ID list from items
    - geometry (str): The geometry in string format.
    - order_dir(str): The directory to save the order.
    - product_bundle (str): The product bundle.
    - directory (str): The directory to save the order.
    '''

    #Authenticate with the Planet API
    auth = get_auth(api_key)

    # create random order name with hour, minute, and second
    order_dir = pathlib.Path(order_dir)
    order_name = f"planetorder_" + datetime.datetime.now().strftime(("%Y-%m-%d_%H-%M-%S"))
    # Create the request
    order_path = order_dir / order_name
    order_path.mkdir(parents=True, exist_ok=True)
    
    # Create the order request
    async with planet.Session(auth=auth) as sess:
        client_order = sess.client("orders")
        # Open the item list
        item_list = [str(item) for item in item_list.split(",")]

        request = create_request(
            item_type,
            item_list,
            geometry,
            order_name,
            product_bundle,
        )

        # Create a folder in your download machine
        # Create and download the order 
        order_filepath = str(order_path) 
        await create_and_download(client_order, request, order_filepath)
        print(f"Order {order_name} has been created and downloaded.")
