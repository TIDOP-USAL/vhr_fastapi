import requests
from datetime import datetime
import json
from natsort import natsorted
now = datetime.now()
catalog=[]
i = 1
def parseurl(url, detail=False):
    global i
    try:
        response = requests.get(url)
        r = response.json()
        gee_id = r["id"]
        print(f"{i}: {gee_id}")
        gee_title = r["title"]
        if "deprecated" in gee_title.lower():
            return
        if "deprecated" in r.keys():
            if r["deprecated"] == True:
                return
        gee_type = r["gee:type"]
        gee_start = r["extent"]["temporal"]["interval"][0][0].split("T")[0]
        if not r["extent"]["temporal"]["interval"][0][1] == None:
            gee_end = r["extent"]["temporal"]["interval"][0][1].split("T")[0]
        else:
            gee_end = now.strftime("%Y-%m-%d")
        gee_start_year = gee_start.split("-")[0]
        gee_end_year = gee_end.split("-")[0]
        gee_provider = r["providers"][0]["name"]
        gee_tags = r["keywords"]
        gee_eobands = r["summaries"]["eo:bands"] if "eo:bands" in r["summaries"].keys() else []
        gee_bands = [x for x in gee_eobands if "name" in x.keys() and "description" in x.keys()]
         # and "gee:scale" in x.keys()
        gee_visualization = r["summaries"]["gee:visualizations"] if "gee:visualizations" in r["summaries"].keys() else []
        img_vis = [x["image_visualization"] for x in gee_visualization if "image_visualization" in x.keys()] if len(gee_visualization) > 0 else []
        
        bands = {}
        if len(gee_bands) > 0:
            gee_band_val = [x["name"] for x in gee_bands if "name" in x.keys()]
            gee_band_desc = [x["description"] for x in gee_bands if "description" in x.keys()]
            gee_band_gsd = [x["gsd"] for x in gee_bands if "gsd" in x.keys()]
            gee_band_scale = [x["gee:scale"] for x in gee_bands if "gee:scale" in x.keys()]
            if len(gee_band_val) > 0: bands["values"] = gee_band_val
            if len(gee_band_desc) > 0: bands["description"] = gee_band_desc
            if len(gee_band_gsd) > 0: bands["gsd"] = gee_band_gsd
            if len(gee_band_scale) > 0: bands["scale"] = gee_band_scale
        
        band_vis = []
        if len(img_vis) > 0:
            band_vis = img_vis[0]["band_vis"] if "band_vis" in img_vis[0].keys() else []

        asset = {
            "id": gee_id,
            "provider": gee_provider,
            "title": gee_title,
            "start_date": gee_start,
            "end_date": gee_end,
            "startyear": gee_start_year,
            "endyear": gee_end_year,
            "type": gee_type,
            "tags": ", ".join(gee_tags),
            "vis": band_vis if len(band_vis) > 0 else [],
        }
        asset["bands"] = bands
        catalog.append(asset)
        i = i + 1
    except Exception as e:
        print(url)
        print(e)

asset_list = []
def yf(url):
    page = requests.get(url)
    if page.status_code == 200:
        features = [
            assets["href"]
            for assets in page.json()["links"]
            if assets["rel"] == "child"
        ]
        print(features)
        for feature in features:
            if not feature.endswith("catalog.json"):
                asset_list.append(feature)
            else:
                yf(feature)

yf(url="https://earthengine-stac.storage.googleapis.com/catalog/catalog.json")

item_list = natsorted(list(set(asset_list)))
try:
    for items in item_list:
        parseurl(items, detail=False)
except Exception as e:
    print(f"Failed for {items}")
    print(e)
finally:
    with open("data/gee_catalog_full.json", "w") as file:
        json.dump(catalog, file, indent=4, sort_keys=True)