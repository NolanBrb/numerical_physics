from subprocess import run

from os import listdir
from os.path import join, isdir
from tqdm import tqdm

out_path = r"E:\Cluster_Sim_Data\out"

list_not_computed = []

for sim in listdir(out_path):
    sim_path = join(out_path, sim)
    if not isdir(sim_path):
        continue
    if not "hydro_parms.json" in listdir(sim_path):
        list_not_computed.append(sim_path)

for not_computed in tqdm(list_not_computed):
    print(f"Running hydro parms computation for sim {not_computed}")
    run(f"python compute_fourier_coefficients.py {not_computed}")
    print("Done !")
