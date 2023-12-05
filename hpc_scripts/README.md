Scripts to execute `caribbean_marine_litter.py` on the HPC server at FSU.

- `nexsan_to_rcc.sh`: transfer velocity fields by ssh
- `run_hpc.sh`: script to launch monthly releases with slurm job arrays. 
	- `sbatch -a 0-119%10 run_hpc.sh`: to run 120 months starting January 2010 with 10 concurrent releases and leave CPU for other team members
