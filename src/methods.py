import nest_asyncio
from typing import Dict, List

import xarray as xr
import rioxarray
import cubo
import os
import tempfile

import numpy as np
# import tensorflow as tf
import rioxarray as rxr

nest_asyncio.apply()

async def get_sentinel2(
    coords: List[float],
    bands: List[str],
    start_date: str,
    end_date: str,
    edge_size: int
):
    '''
    Get Sentinel-2 imagery with the Cubo API.
    
    Args:
    - coords (List[float]): The coordinates to search for.
    - collection (str): The collection to search for.
    - bands (List[str]): The bands to search for.
    - start_date (str): The start date for the search.
    - end_date (str): The end date for the search.
    - edge_size (int): The edge size.
    
    Returns:
    - str: The path to the downloaded files.
    '''
    da = cubo.create(
        lat=coords[0],
        lon=coords[1],
        collection="sentinel-2-l2a",
        bands=bands,
        start_date=start_date,
        end_date=end_date,
        edge_size=edge_size,
        units="px",
        resolution=10
    )

    dates = da.time.values.astype("datetime64[D]").astype(str).tolist()
    temp_path = tempfile.mkdtemp()
    list_path = []
    for i in range(0, len(dates)):
        path_image = f"{temp_path}/image_{dates[i]}.tif"
        da[i].rio.to_raster(path_image)
        list_path.append(path_image)

    return list_path

# async def get_sr_from_s2(temp_path: str) -> str:
#     model = tf.saved_model.load("weights/sr4rs_sentinel2_bands4328_france2020_savedmodel")
#     signature = list(model.signatures.keys())[0]
#     func = model.signatures[signature]

#     folder_list = os.listdir(temp_path)
#     path_list = []
#     for i in folder_list:
#             # dataset = opensr_test.load("naip")
#             # lr_dataset, hr_dataset = dataset["L2A"], dataset["HRharm"]
#             lr = np.load("lr_dataset.npy") # Viene de lr_dataset
#             # rioxarray.open_rasterio("image.tif")
#             lr_test = lr[2][[3, 2, 1, 7]][None].transpose(0, 2, 3, 1)

#             Xtf = tf.convert_to_tensor(lr_test, dtype=tf.float32)
#             pred = func(Xtf)

#             # Save the results
#             # pred_np = pred['output_32:0'].numpy()
#             # pred_torch = torch.from_numpy(pred_np).permute(0, 3, 1, 2)
#             # pred_torch_padded = torch.nn.functional.pad(
#             #     pred_torch,
#             #     (32, 32, 32, 32),
#             #     mode='constant',
#             #     value=0,
#             # ).squeeze().numpy().astype('uint16')
#             path_sr = f"{temp_path}/sr_{i}.tif"
#             da[i].rio.to_raster(path_sr)
#             path_list.append(path_sr)

#     return path_list


# async def get_classes():
#     '''
#     DYNNET
#     '''
#     return ["class1", "class2", "class3"]