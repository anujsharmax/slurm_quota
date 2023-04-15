# Slurm - Quota

Toy example to provide equal cpu core guarantee to all users in slurm job scheduler. 

The script rebalance_queue.py can be executed manually or using a cron job (after regular interval) to rebalance the job queue - it prempts jobs for users who are running jobs more than their quota to start the jobs for users who are below their quota and whose jobs are pending.

Note: this repo was created for experimentation and is not suitable for production use-cases.


## Setup

To start the slurm cluster
``` shell
./start.sh
```


To cleanup the slurm cluster
``` shell
./stop.sh
```

## Usage

login to slurmctld node
``` shell
docker exec -it slurmctld bash

# to change user
# su - user1
```

job submission script for doing nothing (1.sh, 2.sh)
``` shell
#!/bin/sh
sleep infinity
```


## Demo

``` shell
# 4 nodes with 1 cpu core each
[root@slurmctld code]# sinfo
PARTITION AVAIL  TIMELIMIT  NODES  STATE NODELIST
normal*      up 5-00:00:00      4   idle c[1-4]

# start with an empty queue
[root@slurmctld code]# squeue
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
			 
# submit 4 jobs from user 1 - quota is 2, overquota is 2
[user1@slurmctld data]$ sbatch -N1 ./1.sh 
Submitted batch job 1
[user1@slurmctld data]$ sbatch -N1 ./1.sh 
Submitted batch job 2
[user1@slurmctld data]$ sbatch -N1 ./1.sh 
Submitted batch job 3
[user1@slurmctld data]$ sbatch -N1 ./1.sh 
Submitted batch job 4

# all jobs are running for user1
[root@slurmctld code]# squeue
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
                 1    normal     1.sh    user1  R       0:10      1 c1
                 2    normal     1.sh    user1  R       0:07      1 c2
                 3    normal     1.sh    user1  R       0:07      1 c3
                 4    normal     1.sh    user1  R       0:07      1 c4
				 
				 
# submit 2 jobs from user 2 - quota is 2, overquota is 2
[user2@slurmctld data]$ sbatch -N1 ./2.sh 
Submitted batch job 5
[user2@slurmctld data]$ sbatch -N1 ./2.sh 
Submitted batch job 6

# both jobs from user 2 are in pending state - this is the default behaviour of slurm
[root@slurmctld code]# squeue
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
                 5    normal     2.sh    user2 PD       0:00      1 (Resources)
                 6    normal     2.sh    user2 PD       0:00      1 (Priority)
                 1    normal     1.sh    user1  R       2:00      1 c1
                 2    normal     1.sh    user1  R       1:57      1 c2
                 3    normal     1.sh    user1  R       1:57      1 c3
                 4    normal     1.sh    user1  R       1:57      1 c4

# run the rebalance_queue.py script
[root@slurmctld code]# python3 /code/rebalance_queue.py 
start
processing: priority_jobs: 2, premptible_jobs: 2
processing: priority_jobs: 1, premptible_jobs: 1
processing: priority_jobs: 0, premptible_jobs: 0
done

# now, the two jobs from user2 are running as well, and the youngest jobs from user1 are prempted (since they were batch jobs, they were requeued)
[root@slurmctld code]# squeue
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
                 3    normal     1.sh    user1 PD       0:00      1 (BeginTime)
                 4    normal     1.sh    user1 PD       0:00      1 (BeginTime)
                 1    normal     1.sh    user1  R       2:50      1 c1
                 2    normal     1.sh    user1  R       2:47      1 c2
                 5    normal     2.sh    user2  R       0:05      1 c4
                 6    normal     2.sh    user2  R       0:04      1 c3
				 
# lets say that the user2 jobs finish or get cancelled
[user2@slurmctld data]$ scancel 5
[user2@slurmctld data]$ scancel 6

# now the suspended jobs from user1 are running again since resources are available
[root@slurmctld code]# squeue
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
                 1    normal     1.sh    user1  R       4:57      1 c1
                 2    normal     1.sh    user1  R       4:54      1 c2
                 3    normal     1.sh    user1  R       0:06      1 c3
                 4    normal     1.sh    user1  R       0:06      1 c4
```

