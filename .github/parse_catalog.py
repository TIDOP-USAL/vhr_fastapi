import json
import pandas as pd

data_path = "data/gee_catalog_full.json"
with open(data_path) as f:
    data = json.load(f)

ids = [x["id"] for x in data]
bands = [x["bands"] for x in data]
tags = [x["tags"] for x in data]
types = [x["type"] for x in data]
titles = [x["title"] for x in data]
vis = [x["vis"] for x in data]

df = pd.DataFrame({"id": ids, "bands": bands, "tags": tags, "type": types, "title": titles})
df["MISSION"] = df.apply(lambda x: x["id"].split("/")[0], axis=1)
df["PRODUCT"] = df.apply(lambda x: "/".join(x["id"].split("/")[1:]), axis=1)
df["title"] = df.apply(lambda x: x["title"].replace("Google Earth Engine: ", ""), axis=1)

df["has_bands"] = df.apply(lambda x: len(x["bands"]) > 0, axis=1)
df["band_values"] = df.apply(lambda x: x["bands"]["values"] if x["has_bands"] else None, axis=1)
df["band_description"] = df.apply(lambda x: x["bands"]["description"] if x["has_bands"] else None, axis=1)
df["band_scale"] = df.apply(lambda x: x["bands"]["scale"] if x["has_bands"] and "scale" in x["bands"].keys() else None, axis=1)
df["gee_type"] = df.apply(lambda x: x["type"], axis=1)
df["gee_vis"] = vis
df = df[df["id"].str.contains("landsat|sentinel|modis|aster|srtm") | df["tags"].str.contains("landsat|sentinel|modis|aster|srtm")]
# df = df[~((df["type"] == "image_collection") & (df["has_bands"] == False))]

df2 = df[["MISSION", "PRODUCT", "title", "band_values", "band_description", "band_scale", "gee_type", "gee_vis"]]
df2.to_json("data/gee_catalog.json", orient="records")
df2.to_json("public/gee_catalog.json", orient="records")
