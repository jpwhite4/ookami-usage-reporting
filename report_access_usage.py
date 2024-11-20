#/usr/bin/env python3

from configparser import ConfigParser
import argparse
import logging
import csv
import re

import amieclient

logger = logging.getLogger(__name__)


def process_jobs(filename, resource):
    project_re = re.compile(r'^pn_[a-z]{3}[0-9]{6}$')

    with open(filename, 'r') as filep:
        slurmreader = csv.DictReader(filep, fieldnames=['JobID','User','Account','Submit','Start','End','NNodes','ncpus','ElapsedRaw','partition','jobname'], delimiter='|')
        for row in slurmreader:

            if not project_re.match(row['Account']):
                logger.debug('Skip %s due to non-ACCESS project.', row['JobID'])
                continue

            if int(row['ElapsedRaw']) == 0:
                logger.debug('Skip %s due to non-usage.', row['JobID'])
                continue

            yield {
                "Resource": resource,
                "LocalRecordID": row['JobID'],
                "Username": row['User'],
                "LocalProjectID": row['Account'].upper()[3:],
                "SubmitTime": row['Submit'] + 'Z',
                "StartTime": row['Start'] + 'Z',
                "EndTime": row['End'] + 'Z',
                "Charge": int(row['NNodes']) * int(row['ElapsedRaw']) / 3600,
                "Attributes": {
                    "NodeCount": int(row['NNodes']),
                    "CpuCoreCount": int(row['ncpus']),
                    "Queue": row['partition'],
                    "JobName": row['jobname']
                }
            }

class CombinedFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

def main():

    parser = argparse.ArgumentParser(
        prog='report_access_usage.py',
        formatter_class=CombinedFormatter,
        description="""
Read a slurm job log and use the data to send to the Allocations usage API.

Slurm logs should be generated with the following command:

module load slurm
SLURM_TIME_FORMAT="%Y-%m-%dT%H:%M:%S" TZ=UTC sacct --allclusters --allusers \\
    --parsable2 --noheader --allocations --duplicates \\
    --format JobID,User,Account,Submit,Start,End,NNodes,ncpus,ElapsedRaw,partition,jobname \\
    --starttime 2024-06-07T00:00:00 --endtime 2024-09-07T23:59:59 \\
  > slurm_jobs.log

where the starttime and endtime should be set to the desired value.

Then load this into the Allocations Usage database with:

[PATH TO AMIECLIENT python3]/report_access_usage.py slurm_jobs.log

"""
    )

    parser.add_argument('--dryrun', help='Operate in dry run mode. This will parse the file and process it but not send data to the usage API.', action='store_true')
    parser.add_argument('--amieconfig', help='Path to the AMIE usage client configuration file', default='/lustre/projects/hpc_support_ookami/AMIE/config.ini')
    parser.add_argument('--site', help='Name of the AMIE configuration file section to use', default='StonyBrook')

    parser.add_argument('FILENAME', help='name of the file containing sacct log records')
    parser.add_argument('-v', help='Log Verbosity level such as WARN, INFO, DEBUG', default='INFO')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%dT%H:%M:%S', level=args.v)
    logging.captureWarnings(True)

    # Read config file
    config = ConfigParser()
    config.read(args.amieconfig)
    config = config[args.site]

    usage_client = amieclient.UsageClient(
        site_name=config['site_name'],
        api_key=config['api_key'],
        usage_url=config['usage_url']
    )

    record_count = 0
    for job in process_jobs(args.FILENAME, config['resource']):
        record = amieclient.usage.ComputeUsageRecord.from_dict(job)
        record_count += 1
        if args.dryrun:
            print(record.json())
            continue

        for response in usage_client.send(record):
            response = response.as_dict()
            for failed_record in response.get('ValidationFailedRecords', []):
                logger.warn(failed_record)

        if record_count % 100 == 0:
            logging.info(f"Sent {record_count} records.")
    
    logging.info(f"Sent {record_count} records.")

    status = usage_client.status()

    logging.info(status.as_list())

if __name__ == "__main__":
    main()
