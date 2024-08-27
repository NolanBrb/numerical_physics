import xarray as xr
import json
import numpy as np

from os import listdir
from os.path import join, isdir
from tqdm import tqdm


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


out_path = r"E:\Cluster_Sim_Data\out"

attr_dic = {}

for sim in tqdm(listdir(out_path)):
    sim_path = join(out_path, sim)
    if not isdir(sim_path):
        continue
    try:
        ds = xr.open_dataset(join(sim_path, "pcf.nc"))
    except FileNotFoundError:
        print(f"No file was found for sim {sim}")
        continue
    attr_dic[sim] = ds.attrs

with open(join(out_path, "sim_attrs.json"), "w") as jsonFile:
    json.dump(attr_dic, jsonFile, cls=NpEncoder)
