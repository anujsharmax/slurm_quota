#!/usr/bin/env python3

import json
import subprocess
import time


# equal quota for each user on a 4 node cluster, where each node has 1 cpu
QUOTA_CPUS = 2


def get_jobs():
    result = subprocess.run(["squeue", "--json"], stdout=subprocess.PIPE)
    result.check_returncode()
    return json.loads(result.stdout)['jobs']


def filter_jobs(jobs, quota_cpus):
    priority_jobs = []
    premptible_jobs = []
    user_cpus = {}
    for job in jobs:
        if (job['job_state'] == 'RUNNING'):
            user_cpus[job['user_id']] = user_cpus.get(job['user_id'], 0) + job['cpus']
            if user_cpus.get(job['user_id'], 0) > quota_cpus:
                premptible_jobs.append(job)
        if (job['job_state'] == 'PENDING'):
            if (job['cpus'] + user_cpus.get(job['user_id'], 0) <= quota_cpus):
                priority_jobs.append(job)
    return priority_jobs, premptible_jobs


def cancel_job(job_id):
    result = subprocess.run(["scontrol", "cancel", str(job_id)], stdout=subprocess.PIPE)
    result.check_returncode()

def requeue_job(job_id):
    result = subprocess.run(["scontrol", "requeue", str(job_id)], stdout=subprocess.PIPE)
    result.check_returncode()


print('start')

while True:
    jobs = get_jobs()
    priority_jobs, premptible_jobs = filter_jobs(jobs, QUOTA_CPUS)
    print(f'processing: priority_jobs: {len(priority_jobs)}, premptible_jobs: {len(premptible_jobs)}')
    if not priority_jobs:
        break

    premptible_job = premptible_jobs[-1]
    if premptible_job['batch_flag']:
        requeue_job(premptible_job['job_id'])
    else:
        cancel_job(premptible_job['job_id'])

    # don't overwhelm slurm
    time.sleep(1)

print('done')
