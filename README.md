# Grab historical slurm logs


```
module load slurm
SLURM_TIME_FORMAT=%s TZ=UTC sacct --allclusters --allusers \
    --parsable2 --noheader --allocations --duplicates \
    --format JobID,User,Account,Submit,Start,NNodes,ElapsedRaw,partition,jobname \
    --starttime 2024-06-07T00:00:00 --endtime 2024-09-07T23:59:59 \
    > historical_jobs.log
```

Then run the python script to read in the jobs file
```
[PATH TO PYTHON] report_access_usage.py slurm_jobs.log
```
