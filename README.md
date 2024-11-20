# Ookami Usage Reporting

Example script that can be used to report HPC usage on SBU Ookami to the ACCESS Allocations
usage API.

## Usage

The script expects to process a slurm `sacct` log file with specific fields. Create
the log file as follows (update the start and end time parameters to
select the time range of jobs to process).

```
module load slurm
SLURM_TIME_FORMAT=%s TZ=UTC sacct --allclusters --allusers \
    --parsable2 --noheader --allocations --duplicates \
    --format JobID,User,Account,Submit,Start,NNodes,ElapsedRaw,partition,jobname \
    --starttime 2024-06-07T00:00:00 --endtime 2024-09-07T23:59:59 \
    > slurm_jobs.log
```

Then run the python script to read in the jobs file
```
[PATH TO PYTHON] report_access_usage.py slurm_jobs.log
```

## Command line options

```
[PATH TO AMIECLIENT python3]/report_access_usage.py slurm_jobs.log

positional arguments:
  FILENAME              name of the file containing sacct log records

options:
  -h, --help            show this help message and exit
  --dryrun              Operate in dry run mode. This will parse the file and process it but not send data to the usage API. (default: False)
  --amieconfig AMIECONFIG
                        Path to the AMIE usage client configuration file
  --site SITE           Name of the AMIE configuration file section to use
  -v V                  Log Verbosity level such as WARN, INFO, DEBUG (default: INFO)
```
