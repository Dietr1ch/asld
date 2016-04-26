#!/bin/sh

mkdir -p  "bench/crap"
mv *.json "bench/crap"

benchDir="bench/$(date -Iseconds)/"
mkdir -p  "$benchDir"


queries="$(seq 0  15)"

for b in 1 5 10 20 40 80; do

	echo "Running A* b=$b"
	for i in $queries; do
	#for i in 4 8 9 10 12 14 15 16 17 18; do
		timeout --kill-after 4100 3600 ./run.py -w 1 -q $i --pool-size $b --time 3000  $@
		echo "Waiting a bit..."
		sleep 30
	done

	echo "Running Dijstra b=$b"
	for i in $queries; do
	#for i in 4 8 9 10 12 14 15 16 17 18; do
		timeout --kill-after 4100 3600 ./run.py -w 0 -q $i --pool-size $b --time 3000  $@
		echo "Waiting a bit..."
		sleep 30
	done
done

mv *.json "$benchDir"
