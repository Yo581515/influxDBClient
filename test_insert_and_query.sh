#!/usr/bin/env bash
# test_insert_and_query.sh
# Portable test script for TimescaleDB (Postgres+Timescale), InfluxDB, Grafana
# Works on macOS, Linux, and WSL.
# Usage: chmod +x test_insert_and_query.sh && ./test_insert_and_query.sh

set -euo pipefail

# === Configuration (match your docker-compose.yml) ===
INFLUX_CONTAINER="influxdb"
INFLUX_ORG="example-org"
INFLUX_BUCKET="example-bucket"
INFLUX_TOKEN="super-secret-token"

# Optional: set this if your InfluxDB requires a token (recommended for InfluxDB 2.x)
export INFLUX_TOKEN="super-secret-token"

# === Start stack ===
echo "Starting docker compose (if not already running)..."
docker compose up -d

# === Wait for InfluxDB HTTP API to be healthy ===
echo
echo "Waiting for InfluxDB HTTP API to be healthy..."
attempt=0
max_attempts=60
while true; do
  attempt=$((attempt+1))
  set +e
  status=$(docker exec "${INFLUX_CONTAINER}" sh -lc \
    "curl -sS -o /dev/null -w '%{http_code}' http://localhost:8086/health" 2>/dev/null || echo "000")
  set -e

  if [ "${status}" = "200" ]; then
    break
  fi

  echo "  waiting for influxdb... attempt ${attempt}/${max_attempts} (status=${status})"
  if [ "${attempt}" -ge "${max_attempts}" ]; then
    echo "InfluxDB did not become healthy in time. Check container logs: docker logs ${INFLUX_CONTAINER}"
    exit 1
  fi
  sleep 2
done
echo "InfluxDB appears healthy."

# === Token args (only if INFLUX_TOKEN is set) ===
INFLUX_TOKEN_ARGS=()
if [ "${INFLUX_TOKEN:-}" != "" ]; then
  echo "Using InfluxDB token for authentication."
  INFLUX_TOKEN_ARGS+=(--token "${INFLUX_TOKEN}")
fi
# === debug token args value
echo "INFLUX_TOKEN_ARGS=${INFLUX_TOKEN_ARGS[@]}"
echo ""


# === Write sample points to InfluxDB (portable, safe) ===
echo "Writing 3 points to InfluxDB bucket=${INFLUX_BUCKET}..."

TS1=$(python3 - <<'PY'
import time
print(int(time.time() - 5*60))
PY
)

TS2=$(python3 - <<'PY'
import time
print(int(time.time() - 2*60))
PY
)

TS3=$(python3 - <<'PY'
import time
print(int(time.time()))
PY
)

{
  printf "temperature,sensor_id=1 value=21.7 %s\n" "$TS1"
  printf "temperature,sensor_id=1 value=22.1 %s\n" "$TS2"
  printf "temperature,sensor_id=1 value=22.6 %s\n" "$TS3"
} | docker exec -i "${INFLUX_CONTAINER}" influx write \
  --org "${INFLUX_ORG}" \
  --bucket "${INFLUX_BUCKET}" \
  --precision s \
  "${INFLUX_TOKEN_ARGS[@]}" \
  -

# === Query InfluxDB: last 1 hour and latest point (Flux) ===
echo
echo "=== InfluxDB: last 1 hour (flux) ==="
docker exec -i "${INFLUX_CONTAINER}" influx query \
  --org "${INFLUX_ORG}" \
  --raw \
  "${INFLUX_TOKEN_ARGS[@]}" \
  - <<'FLUX'
from(bucket:"example-bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "temperature")
  |> filter(fn: (r) => r._field == "value")
  |> sort(columns: ["_time"])
FLUX

echo
echo "=== InfluxDB: latest point (flux) ==="
docker exec -i "${INFLUX_CONTAINER}" influx query \
  --org "${INFLUX_ORG}" \
  --raw \
  "${INFLUX_TOKEN_ARGS[@]}" \
  - <<'FLUX'
from(bucket:"example-bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "temperature")
  |> filter(fn: (r) => r._field == "value")
  |> sort(desc: true, columns: ["_time"])
  |> limit(n: 1)
FLUX

echo
echo "All done. If you saw rows for TimescaleDB and points for InfluxDB, your stack is working."