#!/bin/bash
# ==============================================================================
# ContentForge AI Headless Load Testing Runner
# Simulates 50 concurrent users issuing /generate requests against the API
# ==============================================================================

set -e

HOST_URL="${1:-http://localhost:8000}"
USERS="${2:-50}"
SPAWN_RATE="${3:-10}"
RUN_TIME="${4:-30s}"

echo "================================================================================"
echo "ContentForge AI - Locust Load Test"
echo "Target Host:  $HOST_URL"
echo "Concurrency:  $USERS users"
echo "Spawn Rate:   $SPAWN_RATE users/sec"
echo "Duration:     $RUN_TIME"
echo "================================================================================"

locust -f "$(dirname "$0")/locustfile.py" \
  --headless \
  --users "$USERS" \
  --spawn-rate "$SPAWN_RATE" \
  --run-time "$RUN_TIME" \
  --host "$HOST_URL" \
  --html "$(dirname "$0")/load_test_report.html" \
  --csv "$(dirname "$0")/load_test_results"

echo "Load test finished. Reports generated in $(dirname "$0")/"
