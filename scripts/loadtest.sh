#!/bin/sh
# Usage: sh scripts/loadtest.sh <run-name> [threads] [seconds]
# Runs the JMeter plan against the gateway and writes an HTML report to loadtest/results/<run-name>/
RUN=${1:?run name, e.g. run02}; THREADS=${2:-150}; SECS=${3:-60}
rm -rf "loadtest/results/$RUN" "loadtest/results/$RUN.jtl"; mkdir -p loadtest/results
docker compose run --rm jmeter -n -t /loadtest/read-load.jmx -Jthreads="$THREADS" -Jduration="$SECS" \
  -l "/loadtest/results/$RUN.jtl" -e -o "/loadtest/results/$RUN" > /dev/null
python3 - "$RUN" <<'PY'
import csv, sys, statistics
run = sys.argv[1]
rows = list(csv.DictReader(open(f"loadtest/results/{run}.jtl")))
t = sorted(int(r["elapsed"]) for r in rows)
err = [r for r in rows if r["success"] != "true"]
codes = {}
for r in err: codes[r["responseCode"]] = codes.get(r["responseCode"], 0) + 1
p = lambda q: t[min(len(t) - 1, int(q * len(t)))]
secs = (int(rows[-1]["timeStamp"]) - int(rows[0]["timeStamp"])) / 1000 or 1
print(f"LOAD TEST {run}: {len(rows):,} requests in {secs:.0f}s ({len(rows)/secs:,.0f}/s)")
print(f"  latency  median {statistics.median(t):.0f}ms   p95 {p(0.95)}ms   p99 {p(0.99)}ms")
print(f"  errors   {len(err):,} ({100*len(err)/len(rows):.2f}%)  {codes or ''}")
print(f"  HTML report: loadtest/results/{run}/index.html")
PY
