import nest_asyncio
import planet
from utils import (get_auth, create_filters, create_request, create_and_download, 
                   query_data, create_folder_and_txt)
from basemodels import ItemDict
from typing import Dict
import pathlib
import numpy as np
import rasterio as rio

# Libraries needed for th Dynnet model
import torch
from helper import parser
from utils.setup_helper import make_deterministic
from data.utae_dynamicen import DynamicEarthNet
from network.models import define_model

nest_asyncio.apply()

async def query_datalist(
    api_key: str,
    geometry: str,
    edge_size: int,
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
    - edge_size (int): The size of the square edge.
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
    sfilter = create_filters(geometry, edge_size, start_date, end_date, 
                             cloud_cover)
    
    # Get the items that match the filters
    items_dicts = await query_data(auth, item_type, sfilter, asset)
    
    return items_dicts


async def create_download(
    api_key: str,
    item_type: str,
    item_list: str,
    geometry: str,
    edge_size: int,
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
    - edge_size (int): The edge size of the image.
    - order_dir(str): The directory to save the order.
    - product_bundle (str): The product bundle.
    - directory (str): The directory to save the order.
    '''

    #Authenticate with the Planet API
    auth = get_auth(api_key)

    # create random order name with hour, minute, and second
    order_dir = pathlib.Path(order_dir)
   
    # Create the order request
    async with planet.Session(auth=auth) as sess:
        client_order = sess.client("orders")
        # Open the item list
        item_list = [str(item) for item in item_list.split(",")]

        request = create_request(
            item_type,
            item_list,
            geometry,
            edge_size,
            product_bundle
        )

        # Create a folder in your download machine
        # Create and download the order 
        order_id = await create_and_download(client_order, request, order_dir)
        print(f"Order {order_id} has been created and downloaded.")

        
def process_image(
    api_key: str,
    item_type: str,
    item_list: str,
    geometry: str,
    edge_size: int,
    order_dir: str,
    product_bundle: str
) -> np.array:
    '''
    Process the image with UTAE model (for Dynnet) using the Planet API.
    More info related to the model can be found at: https://github.com/aysim/dynnet
    
    Args:
    - api_key (str): The Planet API key.
    - item_type (str): The item type.
    - item_list (str): Get the ID list from items
    - geometry (str): The geometry in string format.

    Returns:
    - np.array: The output classes.
    '''
    # Create and download image
    order_id = create_download(api_key, item_type, item_list, geometry, edge_size,
                               order_dir, product_bundle)

    # Locate the image in the selected directory
    order_dir = pathlib.Path(order_dir)
    folder = order_dir / order_id 

    # To run this model, we need: a txt with the following structure
    # image_name
    # - input
    # -- image1.tif 20XX-XX-01
    # -- image2.tif 20XX-XX-05
    # -- image3.tif 20XX-XX-10
    # -- image4.tif 20XX-XX-15
    # -- image5.tif 20XX-XX-20
    # -- image6.tif 20XX-XX-25

    # - label
    # -- label1.tif 20XX-XX-01
    # -- label2.tif 20XX-XX-05
    # -- label3.tif 20XX-XX-10
    # -- label4.tif 20XX-XX-15
    # -- label5.tif 20XX-XX-20
    # -- label6.tif 20XX-XX-25

    # The .txt seems like this:
    # /input /label/20XX-XX-01.tif 20XX-XX
    # /input /label/20XX-XX-05.tif 20XX-XX
    # /input /label/20XX-XX-10.tif 20XX-XX
    # /input /label/20XX-XX-15.tif 20XX-XX
    # /input /label/20XX-XX-20.tif 20XX-XX
    # /input /label/20XX-XX-25.tif 20XX-XX

    # The idea is copy the image five times and change the date in the txt
    # The label are not used to predict, so can we full of zeros

    # Somewhere in the code, these variables are defined
    # Create the folder and txt to the folder
    
    root_folder = create_folder_and_txt(root="data", image_folder=folder)

    # Parse the model
    parse = parser.Parser()
    opt, _ = parse.parse()
    opt.is_Train = False
    make_deterministic(opt.seed)
    config = parser.read_yaml_config(opt.config)

    # Put the args
    data_config = config['DATA']
    data_config['ROOT'] = root_folder
    data_config['EVAL_SUBSET'] = 'test'
    model = "utae"
    ckpt_path = "dynnet_ckpt/utae/weekly/best_ckpt.pth"
        
    # Clear cuda memory
    torch.cuda.empty_cache()


    # Load the data
    dataset = DynamicEarthNet(root=data_config['ROOT'], mode=data_config['EVAL_SUBSET'], type=data_config['TYPE'],
                            crop_size=data_config['RESIZE'], num_classes=data_config['NUM_CLASSES'],
                            ignore_index=data_config['IGNORE_INDEX'])

    test_loader = torch.utils.data.DataLoader(dataset, batch_size=config['EVALUATION']['BATCH_SIZE'], 
                                            shuffle=False,
                                            num_workers=data_config['NUM_WORKERS'], 
                                            pin_memory=True)
    
    # Select the batch
    for i, data in enumerate(test_loader):
        if i == 0:  # 0 is the first batch, 1 is the second batch and so on
            batch = data
            break
    
    # Unpack the batch and ensure that the data is in the GPU
    input, label = batch
    data = input[0].cuda()
    label = label[0].cuda()

    # Load the pretrained model
    config['NETWORK']['NAME'] = model
    network = define_model(config, model=config['NETWORK']['NAME'], gpu_ids=opt.gpu_ids)
    network.load_state_dict(torch.load(ckpt_path)["model_dict"])

    # Set the model to evaluation mode
    network.eval()

    # Infer the data

    with torch.no_grad():       
        input = data[:,0,...].unsqueeze(0)
        zeros_images = torch.zeros(1, 5, 4, edge_size, edge_size).cuda() 
        input = torch.cat((input, zeros_images), dim=1) ## E.g. in format 1, 6, 4, 128, 128
        
        logit = network(input)
        output = torch.sigmoid(logit)
        output_np = output[0].cpu().numpy()
        output_classes = np.argmax(output_np, axis=0).astype(np.int8)

    ## Save in output folder
    output_folder = root_folder / "output"
    output_folder.mkdir(parents=True, exist_ok=True)

    # Get the parent folder
    parent_folder = root_folder.parent

    with rio.open(root_folder / "input/composite_udm2.tif") as src:
        profile = src.profile
        class_profile = profile.copy()
        class_profile.update(dtype=rio.uint8, count=1)

        with rio.open(output_folder / f"output_{str(parent_folder)}.tif", 
                    "w", **class_profile) as dst2:
            dst2.write(output_classes)

    return output_classes
