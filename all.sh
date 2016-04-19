#!/bin/sh

b="$PWD"
benchDir="bench/$(date -Ihours)"
mkdir -p "$benchDir"

queries="$(seq 0  15)"

echo "Running A*"
for i in $queries; do
	timeout --kill-after 4100 3600 ./run.py -w 1 -q $i  $@
	echo "Waiting a bit..."
	sleep 30
done

echo "Running Dijstra"
for i in $queries; do
	timeout --kill-after 4100 3600 ./run.py -w 0 -q $i  $@
	echo "Waiting a bit..."
	sleep 30
done

