#!/bin/bash

source venv/scripts/activate

export PYTHONPATH=$(pwd)

# set -a
# source .env.mongodb
# set +a
# echo "env variables loaded from .env.mongodb"


# set -a
# source .env.benchmark_db
# set +a
# echo "env variables loaded from .env.benchmark_db"


# set -a
# source .env.timescaledb
# set +a
# echo "env variables loaded from .env.timescaledb"

set -a
source .env.influxdb
set +a
echo "env variables loaded from .env.influxdb"