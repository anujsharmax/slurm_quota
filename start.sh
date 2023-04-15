#!/usr/bin/env bash
set -e

docker compose build
docker-compose up -d

# wait for all services to be up
sleep 5
./submodules/slurm-docker-cluster/register_cluster.sh

# setup slurm accounts for user1 and user2
docker exec slurmctld bash -c "/usr/bin/sacctmgr --immediate create user user1 defaultaccount=root adminlevel=[None] && /usr/bin/sacctmgr --immediate create user user2 defaultaccount=root adminlevel=[None]"
