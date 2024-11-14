import os
import cubo
import tempfile
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

import nest_asyncio

# import tensorflow as tf
import rioxarray as rxr

from typing import Dict, List
from skimage import exposure
from datetime import datetime

import torch
from torchvision import transforms
from super_image import HanModel
from segmentation_models_pytorch import Unet

nest_asyncio.apply()

def load_model_sr():
    model = HanModel.from_pretrained('weights/han', scale=4)
    return model

def load_model_build():
    model = torch.load("weights/mitb1_building_unet_best_model.pth", map_location=torch.device("cpu"))
    return model

# def load_model_roads():
#     model = torch.load("weights/mit_b1unet_best_model.pth")
#     return model

async def get_sentinel2(
        lat: float,
        lon: float,
        bands: List[str],
        start_date: str,
        end_date: str,
        edge_size: int
    ):
    da = cubo.create(
        lat=lat,
        lon=lon,
        collection="sentinel-2-l2a",
        bands=bands,
        start_date=start_date,
        end_date=end_date,
        edge_size=edge_size,
        units="px",
        resolution=10,
        query={"eo:cloud_cover": {"lt": 50}}
    )

    dates = da.time.values.astype("datetime64[D]").astype(str).tolist()

    # tempfile.tempdir = os.getcwd() + "/public"
    tempfile.tempdir = "/usr/src/app/public/output"
    folder = tempfile.mkdtemp()
    list_path = []
    
    for i in range(0, len(dates)):
        path_image = f"{folder}/image_{dates[i]}.npy"
        data = da[i].to_numpy()
        np.save(path_image, data)
        list_path.append(path_image)
    
    return folder

async def get_sr(folder: str):
    model = load_model_sr()
    model.eval()

    path_list = [folder + "/" + x for x in os.listdir(folder)]
    path_list_sr = []
    print(path_list)

    for path_i in path_list:
        date_eval = path_i.split("/")[-1].split("_")[1].split(".")[0]
        # print(date_eval)
        lr = np.load(path_i)
        lr = lr[0:3] / 10000

        ## Add a padding of 16 pixels
        lr = np.pad(lr, ((0,0),(16, 16),(16, 16)), mode="edge")
        image_torch = torch.from_numpy(lr).float()

        with torch.no_grad():
            sr_img = model(image_torch[None]).squeeze().numpy()

        ## Remove the padding
        super_img = sr_img[:,64:-64,64:-64]

        path_sr = f"{folder}/sr_{date_eval}.npy"
        path_list_sr.append(path_sr)
        np.save(path_sr, super_img)

    return path_list_sr


def preprocess_image_for_inference(image_path, normalize=False, mean=None, std=None):
    image = np.load(image_path).squeeze()
    image = np.moveaxis(image, 0, -1)
    preprocess_pipeline = transforms.Compose([
        transforms.ToTensor()  
    ])
    if normalize and mean is not None and std is not None:
        preprocess_pipeline.transforms.append(transforms.Normalize(mean=mean, std=std))

    image = preprocess_pipeline(image).float()
    image = image.unsqueeze(0)  

    return image

def inference_building(normalize, mean, std, path_to_image, threshold):
    checkpoint = load_model_build()
    model = Unet(encoder_name="mit_b1", in_channels=3, classes=1, encoder_weights=None)  # Set encoder_weights to None
    filter_ckpt = {k: v for k, v in checkpoint.items()}
    
    model.load_state_dict(filter_ckpt)
    model = model.cpu()
    model.eval()

    image = preprocess_image_for_inference(path_to_image, normalize=normalize, mean=mean, std=std).cpu()

    with torch.no_grad():
        output = model(image)
        output = (output > threshold).float()
    output = output.squeeze().numpy()
    return output

async def get_buildings(folder: str):
    path_list = [folder + "/" + x for x in os.listdir(folder)]
    path_buildings = []

    threshold = 0.5
    normalize = True
    mean = [0.2108307 , 0.1849077 , 0.15864254]
    std = [0.05045007, 0.0406715 , 0.03748639]

    for path_i in path_list:
        try:
            date_eval = path_i.split("/")[-1].split("_")[1].split(".")[0]
            print(date_eval)
            pred_np_buildings = inference_building(normalize, mean, std, path_i, threshold)

            path_sr = f"{folder}/build_{date_eval}.npy"
            np.save(path_sr, pred_np_buildings)
            path_buildings.append(path_sr)
        except Exception as e:
            print(e)
            continue
    
    return path_buildings


def normalize_minmax(image):
    image = (image - np.min(image)) / (np.max(image) - np.min(image))
    return image

async def get_vis(folder: str):
    # i = 0
    images = ["{}/{}".format(folder, x) for x in os.listdir(folder) if x.startswith("image")]
    srs = ["{}/{}".format(folder, x) for x in os.listdir(folder) if x.startswith("sr")]
    builds = ["{}/{}".format(folder, x) for x in os.listdir(folder) if x.startswith("build")]
    
    images.sort()
    srs.sort()
    builds.sort()

    for i in range(len(images)):
        date_eval = images[i].split("_")[-1].split(".")[0]
        # "/usr/src/app/src/public/tmp5ebko6_k/s2_2024-09-07.png"

        img_np = np.moveaxis(np.load(images[i]), 0, -1)
        img_np = (img_np / 10000 * 3).clip(0, 1)
        img_np_equalized = exposure.equalize_hist(img_np)

        sr_np = np.moveaxis(np.load(srs[i]), 0, -1)
        sr_np = (sr_np * 3).clip(0, 1)
        sr_np_equalized = exposure.equalize_hist(sr_np)

        build_np = np.load(builds[i])
        build_np = build_np.clip(0, 1)
        
        # Guardar la imagen original individualmente
        plt.imshow(img_np_equalized[:, :, [0, 1, 2]])
        # plt.title("S2 - 10m")
        plt.axis("off")
        image_filename = f"s2_{date_eval}.png"
        image_path = os.path.join(folder, image_filename)
        plt.savefig(image_path)
        plt.close()

        # Guardar la imagen de superresolución individualmente
        plt.imshow(sr_np_equalized[:, :, [0, 1, 2]])
        # plt.title("S2 SR - 2.5m")
        plt.axis("off")
        sr_filename = f"sr_{date_eval}.png"
        sr_path = os.path.join(folder, sr_filename)
        plt.savefig(sr_path)
        plt.close()

        # Guardar la imagen de edificaciones individualmente
        plt.imshow(build_np, cmap="gray")
        # plt.title("Edificaciones")
        plt.axis("off")
        build_filename = f"build_{date_eval}.png"
        build_path = os.path.join(folder, build_filename)
        plt.savefig(build_path)
        plt.close()

        # Guardar la imagen combinada
        fig, ax = plt.subplots(1, 3, figsize=(15, 5))
        ax[0].imshow(img_np_equalized[:, :, [0, 1, 2]])
        # ax[0].set_title("S2 - 10m")
        ax[0].axis("off")
        ax[1].imshow(sr_np_equalized[:, :, [0, 1, 2]])
        # ax[1].set_title("S2 SR - 2.5m")
        ax[1].axis("off")
        ax[2].imshow(build_np, cmap="gray")
        # ax[2].set_title("Edificaciones")
        ax[2].axis("off")
        combined_filename = f"combined_{date_eval}.png"
        combined_path = os.path.join(folder, combined_filename)
        plt.savefig(combined_path)
        plt.close()

    list_path = [os.path.join(folder, x) for x in os.listdir(folder) if x.endswith(".png")]
    return list_path
