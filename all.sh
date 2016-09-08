#!/bin/sh

mkdir -p  "bench/crap"
mv *.json "bench/crap"

benchDir="bench/$(date -Iseconds)/"
mkdir -p  "$benchDir"


#queries="$(seq 0  15)"
#queries="4 8 9 10 12 14 15 16 17 18"
queries="10 12 14 15"

batchSizes="1 5 10 20 40 80 160 320"
#batchSizes="40 80"


timeLimit="3000"
timeGiven="3600"
killTime="4100"


for poolSize in $batchSizes; do

	echo "Running A* b=$b"
	for queryID in $queries; do
		timeout --kill-after $killTime $timeGiven ./run.py -q $queryID --pool-size $poolSize --time $timeLimit  $@
		echo "Waiting a bit..."
		sleep 10
	done

	echo "Running Dijstra b=$b"
	for i in $queries; do
		timeout --kill-after $killTime $timeGiven ./run.py -w 0 -q $queryID --pool-size $poolSize --time $timeLimit  $@
		echo "Waiting a bit..."
		sleep 10
	done
done

mv *.json "$benchDir"
