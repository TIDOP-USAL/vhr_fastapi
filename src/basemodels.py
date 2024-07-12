from typing import Dict, List, Union
from pydantic import BaseModel


# For the FILTER to search items
class AOIDict(BaseModel):
    type: str
    coordinates: List[List[List[float]]]


class GeometryDict(BaseModel):
    type: str
    field_name: str
    config: AOIDict


class DateRangeDict(BaseModel):
    type: str
    field_name: str
    config: Dict[str, str]


class CloudCoverDict(BaseModel):
    type: str
    field_name: str
    config: Dict[str, float]


class SFilterDict(BaseModel):
    type: str
    config: List[Union[GeometryDict, DateRangeDict, CloudCoverDict]]


## For the QUERY DATA
class ItemDict(BaseModel):
    _links: Dict[str, str]
    _permissions: List[str]
    assets: List[str]
    geometry: AOIDict
    id: str
    properties: Dict[str, Union[str, float]]
    type: str


## For the REQUEST ORDER
class ClipDict(BaseModel):
    aoi: AOIDict


class CompositeDict(BaseModel):
    composite: dict


class HarmonizeDict(BaseModel):
    target_sensor: str


class ToolsDict(BaseModel):
    clip: ClipDict
    composite: CompositeDict
    harmonize: HarmonizeDict


class ProductDict(BaseModel):
    Item_ids: List[str]
    item_type: str
    product_bundle: str


class OrderDict(BaseModel):
    name: str
    products: List[ProductDict]
    tools: List[ToolsDict]

# For the FAST API REQUEST
class SearchRequest(BaseModel):
    api_key: str
    geometry_json: str
    item_type: str
    start_date: str
    end_date: str
    cloud_cover: float
    asset: str

class DownloadRequest(BaseModel):
    api_key: str
    geometry_json: str
    item_type: str
    start_date: str
    end_date: str
    cloud_cover: float
    asset: str
    bundle: str