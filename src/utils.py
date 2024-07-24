import asyncio
import json
import pathlib
import planet

from typing import Dict, List, Union
from basemodels import SFilterDict, ItemDict, OrderDict


def identify_and_convert(geometry_json_str):
    # Convertir la cadena JSON a una estructura de datos Python
    coordinates = json.loads(geometry_json_str)
    
    # Determinar el tipo de geometría basado en la estructura de los corchetes
    if isinstance(coordinates, list):
        if all(isinstance(coord, (list, tuple)) and len(coord) == 2 for coord in coordinates):
            # Caso de un conjunto de coordenadas simples: Punto o Línea
            if len(coordinates) == 1:
                return "Point"
            elif coordinates[0] == coordinates[-1]:
                return "Polygon"
            else:
                return "LineString"
            
        else:
            raise ValueError("La estructura de datos no corresponde a una geometría conocida.")
    else:
        raise ValueError("El formato de entrada no es válido.")

    
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
    start_date: str="2021-01-01T00:00:00Z",
    end_date: str="2021-12-31T23:59:59Z",
    cloud_cover: float=0.5,
    logical_filter: str = "AndFilter",
) -> SFilterDict:
    """
    Create filters for the Planet API request.

    Args:
    - geometry (str): The geometry in string format.
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
        "config": {"type": identify_and_convert(geometry), 
                   "coordinates": [json.loads(geometry)]}
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
    order_name: str,
    product_bundle: str = "analytic_sr_udm2",
) -> OrderDict:
    """
    Create an order request for the Planet API.

    Args:
    - item_type (str): The item type.
    - item_lists (List[str]): Get the ID lists
    - geometry (str): The geometry in string format.
    - order_name (str): The name of the order request.
    - product_bundle (str): The product bundle to order.

    Returns:
    - OrderDict: The order request.
    """

    # Create order request
    order = planet.order_request.build_request(
        name=order_name,
        products=[
            planet.order_request.product(
                item_ids=item_list,
                product_bundle=product_bundle,
                item_type=item_type,
            )
        ],
        tools=[
            planet.order_request.clip_tool(aoi={"type": identify_and_convert(geometry), 
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
