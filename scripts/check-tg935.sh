#!/usr/bin/env bash
# Check TG935 flight status from airportinfo.live
# Outputs status line for comparison

set -euo pipefail

DATE="${1:-$(TZ='Europe/Brussels' date +%Y-%m-%d)}"

STATUS=$(curl -s --max-time 15 "https://airportinfo.live/flight/tg935" 2>/dev/null)

# Extract key info
echo "$STATUS" | python3 -c "
import sys, re

html = sys.stdin.read()

# Find status
status_match = re.search(r'Status TG935.*?(\w+)', html, re.DOTALL)
status = status_match.group(1) if status_match else 'unknown'

# Find revised times
dep_match = re.search(r'Revised Departure\s*(\d{1,2}:\d{2})', html)
arr_match = re.search(r'Revised Arrival\s*(\d{1,2}:\d{2})', html)
sched_dep = re.search(r'Scheduled Departure\s*(\d{1,2}:\d{2})', html)
sched_arr = re.search(r'Scheduled Arrival\s*(\d{1,2}:\d{2})', html)

dep = dep_match.group(1) if dep_match else (sched_dep.group(1) if sched_dep else '?')
arr = arr_match.group(1) if arr_match else (sched_arr.group(1) if sched_arr else '?')
s_dep = sched_dep.group(1) if sched_dep else '?'
s_arr = sched_arr.group(1) if sched_arr else '?'

changed = dep != s_dep or arr != s_arr

print(f'status={status}')
print(f'scheduled_dep={s_dep}')
print(f'scheduled_arr={s_arr}')
print(f'revised_dep={dep}')
print(f'revised_arr={arr}')
print(f'changed={changed}')
"
