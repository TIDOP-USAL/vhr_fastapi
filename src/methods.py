import nest_asyncio
from typing import Dict, List

import xarray as xr
import rioxarray as rxr
import cubo
import os
import tempfile
import matplotlib.pyplot as plt

import numpy as np
import tensorflow as tf
import rioxarray as rxr

from skimage import exposure

# import torch
# from torchvision import transforms
# from utae_seg import utae, weight_init

nest_asyncio.apply()

async def get_sentinel2(
        lat: float,
        lon: float,
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
        lat=lat,
        lon=lon,
        collection="sentinel-2-l2a",
        bands=bands,
        start_date=start_date,
        end_date=end_date,
        edge_size=edge_size,
        units="px",
        resolution=10
    )

    dates = da.time.values.astype("datetime64[D]").astype(str).tolist()
    folder = tempfile.mkdtemp()
    list_path = []
    for i in range(0, len(dates)):
        path_image = f"{folder}/image_{dates[i]}.npy"
        data = da[i].to_numpy()
        np.save(path_image, data)
        list_path.append(path_image)
    
    return folder

async def get_sr(folder: str):
    model = tf.saved_model.load("src/weights/sr4rs_sentinel2_bands4328_france2020_savedmodel")
    signature = list(model.signatures.keys())[0]
    func = model.signatures[signature]

    path_list = [folder + "/" + x for x in os.listdir(folder)]
    path_list_sr = []
    print(path_list)

    for path_i in path_list:
        date_eval = path_i.split("/")[-1].split("_")[1].split(".")[0]
        print(date_eval)
        lr = np.load(path_i)
        lr_resized = lr[:,:64,:64] # 4 bands and 64x64 pixels
        lr_test = lr_resized[None].transpose(0, 2, 3, 1)

        Xtf = tf.convert_to_tensor(lr_test, dtype=tf.float32)
        pred = func(Xtf)

        # Save the results
        pred_np = pred['output_32:0'].numpy()
        pred_np_permuted = np.transpose(pred_np, (0, 3, 1, 2)) # 4x192x192 -> 4x192x192x1
        # pred_np_padded = np.pad(
        #     pred_np_permuted,
        #     pad_width=((0, 0), (0, 0), (32, 32), (32, 32)),
        #     mode='constant',
        #     constant_values=0
        # )

        pred_np_permuted_sq = np.squeeze(pred_np_permuted).astype('uint16')
        path_sr = f"{folder}/sr_{date_eval}.npy"
        path_list_sr.append(path_sr)
        np.save(path_sr, pred_np_permuted_sq)

    return path_list_sr

async def get_vis(folder: str):
    # i = 0
    images = ["{}/{}".format(folder, x) for x in os.listdir(folder) if x.startswith("image")]
    srs = ["{}/{}".format(folder, x) for x in os.listdir(folder) if x.startswith("sr")]

    images.sort()
    srs.sort()

    for i in range(len(images)):
        date_eval = images[i].split("_")[-1].split(".")[0]

        img_np = np.moveaxis(np.load(images[i]), 0, -1)
        img_np = (img_np / 10000 * 3).clip(0, 1)
        img_np_equalized = exposure.equalize_hist(img_np)

        sr_np = np.moveaxis(np.load(srs[i]), 0, -1)
        sr_np = (sr_np / 10000 * 3).clip(0, 1)
        sr_np_equalized = exposure.equalize_hist(sr_np)

        # Create a plot for the first image of each collection
        fig, ax = plt.subplots(1, 2, figsize=(10, 5))
        ax[0].imshow(img_np_equalized[:,:, [0,1,2]])
        ax[0].set_title("Image")
        ax[0].axis("off")
        ax[1].imshow(sr_np_equalized[:,:, [0,1,2]])
        ax[1].set_title("Superresolution")
        ax[1].axis("off")

        plt.savefig(f"{folder}/s2_sr_{date_eval}.png")


# async def get_classes(folder: str):
#     weights = "dynnet_ckpt/utae/weekly/best_ckpt.pth" # Path to the weights
#     ## Load the data
#     with open("defaults.yaml", "r") as f:
#         config = yaml.safe_load(f)

#     net = utae.UTAE(input_dim=4,
#                     encoder_widths=config['NETWORK']['ENCODER_WIDTHS'],
#                     decoder_widths=config['NETWORK']['DECODER_WIDTHS'],
#                     str_conv_k=config['NETWORK']['STR_CONV_K'],
#                     str_conv_s=config['NETWORK']['STR_CONV_S'],
#                     str_conv_p=config['NETWORK']['STR_CONV_P'],
#                     agg_mode=config['NETWORK']['AGG_MODE'],
#                     encoder_norm=config['NETWORK']['ENCODER_NORM'],
#                     n_head=config['NETWORK']['N_HEAD'],
#                     d_model=config['NETWORK']['D_MODEL'],
#                     d_k=config['NETWORK']['D_K'],
#                     encoder=False,
#                     return_maps=False,
#                     pad_value=config['NETWORK']['PAD_VALUE'],
#                     padding_mode=config['NETWORK']['PADDING_MODE'])

#     # Initialize the weights
#     init = weight_init.weight_init
#     net.apply(init)
#     state_dict = torch.load(weights,  map_location=torch.device('cpu'))["model_dict"]
#     new_state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
#     net.load_state_dict(new_state_dict)
#     net.eval()

#     ## Normalize the data
#     mean = [1042.59240722656, 915.618408203125, 671.260559082031, 2605.20922851562]
#     std = [957.958435058593, 715.548767089843, 596.943908691406, 1059.90319824218]
#     normalize = transforms.Normalize(mean=mean, std=std)

#     path_list_class = []
#     for path in os.listdir(folder):
#         path_npy = folder + "/" + path
#         pred_torch = torch.load(path_npy)
#         norm_pred = normalize(pred_torch)

#         ## Resize image
#         # pred_resize = image_resize(norm_pred.numpy(), 192) # Multiple of 32

#         ## Predict the image
#         with torch.no_grad():
#             input = torch.from_numpy(norm_pred[None][None])
#             logit = net(input)
#             output = torch.sigmoid(logit)
#             output_np = output[0].cpu().numpy()
#             output_classes = np.argmax(output_np, axis=0).astype(np.int8)
        
#         ## Save the classes
#         path_classes = f"{folder}/classes_{path}.npy"
#         path_list_class.append(path_classes)
#         np.save(path_classes, output_classes)

#     return path_list_class

