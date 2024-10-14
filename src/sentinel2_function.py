from fastapi import APIRouter, HTTPException
from basemodels import DownloadRequest, SearchRequest, SearchRequestS2, SuperResolution
import methods

router = APIRouter()

# DOWNLOAD S2 CUBO
@router.post("/download_s2")
async def download_s2(request: SearchRequestS2):
    """
    This function is used to create and download order for Sentinel-2 Imagery

    Args for request (DownloadRequest): The request model as defined in basemodels.py:
    - coords (List[float]): The coordinates to search for.
    - bands (List[str]): The bands to search for.
    - start_date (str): The start date for the search.
    - end_date (str): The end date for the search.
    - edge_size (int): The edge size.

    return:
    - The path to the downloaded files.
    """

    try:
        return await methods.get_sentinel2(**request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# SUPER RESOLUTION S2
@router.post("/sr_s2")
async def sr_s2(request: SuperResolution):
    """_summary_

    Args:
        request (_type_): _description_
    """
    try:
        return await methods.get_sr(**request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# SUPER RESOLUTION S2
@router.post("/get_vis")
async def get_vis(request: SuperResolution):
    """_summary_

    Args:
        request (_type_): _description_
    """
    try:
        return await methods.get_vis(**request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    