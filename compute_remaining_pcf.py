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
    if not "pcf.nc" in listdir(sim_path):
        list_not_computed.append(sim_path)

for not_computed in tqdm(list_not_computed):
    print(f"Running pcf computation for sim {not_computed}")
    run(f"python compute_pair_correlation_function.py {not_computed} 3 100 61 61")
    print("Done !")
