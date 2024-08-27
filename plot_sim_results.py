import numpy as np
import json
import re
import xarray as xr

from os.path import join

out_path = r"E:\Cluster_Sim_Data\out"

with open(join(out_path, "sim_attrs.json")) as jsonFile:
    sim_attrs = json.load(jsonFile)

phi_arr = np.linspace(0.6, 1.0, 5)
v0_arr = np.linspace(1.0, 3.0, 5)
k_arr = np.linspace(4.0, 10.0, 7)
kc_arr = np.array([3.0])
rep_arr = np.arange(6)

shape = (len(phi_arr), len(v0_arr), len(k_arr), len(kc_arr), len(rep_arr))

hydro_parms = [
    "chi",
    "zeta",
    "kappa",
    "mu",
    "alpha",
    "chi_p",
    "nu1",
    "nu2",
    "upsilon1",
    "upsilon2",
    "xi1",
    "xi2",
    "chi_Q",
]

fill_values = np.empty(shape=shape)
fill_values.fill(np.nan)

ds = xr.Dataset(
    data_vars={
        parm: (["phi", "v0", "k", "kc", "rep"], fill_values) for parm in hydro_parms
    },
    coords={
        "phi": phi_arr,
        "v0": v0_arr,
        "k": k_arr,
        "kc": kc_arr,
        "rep": rep_arr,
    },
)

pattern = "\d+\[(\d+)\].torque6.curie.fr"

for sim, sim_parms in sim_attrs.items():
    rep = int(re.search(pattern, sim).group(1))
    phi = sim_parms["phi"]
    v0 = sim_parms["v0"]
    k = sim_parms["k"]
    kc = sim_parms["kc"]
    with open(join(out_path, sim, "hydro_parms.json")) as jsonFile:
        sim_hydro_parms = json.load(jsonFile)
    for parm, value in sim_hydro_parms.items():
        ds[parm].loc[{"phi": phi, "v0": v0, "k": k, "kc": kc, "rep": rep}] = value

ds_avg = ds.mean(dim="rep", skipna=True)

ds_to_plot = ds_avg.sel(phi=1.0)
