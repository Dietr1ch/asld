#!/bin/sh


b="$PWD"
benchDir="bench/$(date -Iseconds)"
mkdir -p "$benchDir/old"
mv *.json "$benchDir/old"
rmdir "$benchDir/old"


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

mv *.json "$benchDir"
