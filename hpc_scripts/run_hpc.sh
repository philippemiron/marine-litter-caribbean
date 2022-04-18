#!/bin/bash

#SBATCH --job-name="caribbean_mpw"
#SBATCH -t 15:00:00
#SBATCH -p coaps_q
#SBATCH -n 16
#SBATCH -N 1
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL

module load openmpi/4.1.0
module load netcdf
module load anaconda

eval "$(conda shell.bash hook)"
conda activate parcels_mpi

# create array of year/month of all jobs
declare -a year month
for y in {10..21..1}
do
    for m in {1..12..1}
    do
	year+=("$(printf "%02d" $y)")
	month+=("$(printf "%02d" $m)")
    done
done
# get the $SLURM_ARRAY_JOB_ID to set the right year and date
i=$SLURM_ARRAY_TASK_ID
start_date_str="20${year[$i]}-${month[$i]}-01"

# below is constant for all monthly releases
end_date_str="2022-01-01"
output_path="/gpfs/research/coaps/pmiron/caribbean-marine-litter/data/output/cm_uniform"
executable_path="/gpfs/research/coaps/pmiron/caribbean-marine-litter"
basename="cm_uniform"
days_per_run=30

end_date_sec=$(date --date="$end_date_str" "+%s")
c_start_date=$(date --date="$start_date_str +$((t)) days" "+%Y-%m-%d")
c_start_date_sec=$(date --date="$start_date_str +$((t)) days" "+%s")
c_end_date_sec=$(date --date="$start_date_str +$((t+days_per_run)) days" "+%s")

# check if not at the end of simulation
if [ $c_end_date_sec -lt $end_date_sec ]
then
  c_end_date=$(date --date="$start_date_str +$((t+days_per_run)) days" "+%Y-%m-%d")
else
  c_end_date=$(date --date="$end_date_str" "+%Y-%m-%d")
fi

t=0
i=1
while [ $c_start_date_sec -lt $end_date_sec ]
do
  fi=`printf %03d $i`
  fp=`printf %03d $[$i-1]`
  
  if [ $t -eq  0 ]
  then
    # run from initial position
    cmd="srun python $executable_path/caribbean_model.py $c_start_date:0 $c_end_date:0 True True False ${basename}_${start_date_str}_${fi}"
  else
    # start from restart file
    cmd="srun python $executable_path/caribbean_model.py $c_start_date:0 $c_end_date:0 True True False ${basename}_${start_date_str}_${fi} ${output_path}/${basename}_${start_date_str}_${fp}.nc"
  fi
  echo $cmd
  $cmd

  t=$[$t+$days_per_run]
  i=$[$i+1]
  prev_start_date=$c_start_date
  prev_end_date=$c_end_date
  c_start_date=$(date --date="$start_date_str +$((t)) days" "+%Y-%m-%d")
  c_start_date_sec=$(date --date="$start_date_str +$((t)) days" "+%s")
  c_end_date_sec=$(date --date="$start_date_str +$((t+days_per_run)) days" "+%s")
  
  # check if not at the end of simulation
  if [ $c_end_date_sec -lt $end_date_sec ]
  then
      c_end_date=$(date --date="$start_date_str +$((t+days_per_run)) days" "+%Y-%m-%d")
  else
      c_end_date=$(date --date="$end_date_str" "+%Y-%m-%d")
  fi
done

# combine intermediate files
cmd="python $executable_path/tools.py $output_path $basename $start_date_str True True"
echo $cmd
$cmd
