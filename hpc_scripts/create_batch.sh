#!/bin/bash

# This code generates multiple bash files from generalrun_hpc.sh and runs them in parallel

# Iterate years
for y in {10..21..1}
do
    cur_year=$(printf "%02d" $y)
    for m in {1..12..1}
    do
        cur_month=$(printf "%02d" $m)
        sed --expression="s/MONTH/${cur_month}/g" --expression="s/YEAR/${cur_year}/g" default_run_hpc.sh > run20${cur_year}_${cur_month}.sh
        #sbatch run20${cur_year}_${cur_month}.sh
    done
done