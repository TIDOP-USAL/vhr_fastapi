from fastapi import APIRouter, HTTPException
from basemodels import DownloadRequest, SearchRequest
import methods

router = APIRouter()

# POST THUMBNAILS FOR PLANET IMAGERY
@router.post("/search")
async def post_querydata(request: SearchRequest):
    """
    This function is used to query the planet API for imagery

    Args for request (SearchRequest): The request model as defined in basemodels.py:
        - api_key (str): The API key for the planet API
        - geometry(str): The geometry in string format
        - item_type (str): The item type to query
        - start_date (str): The start date for the query. Format: YYYY-MM-DD
        - end_date (str): The end date for the query. Format: YYYY-MM-DD
        - cloud_cover (float): The cloud cover percentage 
        - asset (str): The asset to query. E.g. 'ortho_analytic_4b_sr'
    """

    try:
        return await methods.query_datalist(**request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# DOWNLOAD PLANET IMAGERY
@router.post("/download_planet")
async def download_planet(request: DownloadRequest):
    """
    This function is used to create and download order for Planet Imagery
    
    Args for request (DownloadRequest): The request model as defined in basemodels.py:
    - api_key (str): The API key for the planet API
    - item_type (str): The item type to query
    - item_list (str): Get the ID list from items
    - geometry (str): The geometry in string format
    - order_dir (str): The directory to save the downloaded files
    - product_bundle (str): The product bundle to download
    """

    try:
        return await methods.create_download(**request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
