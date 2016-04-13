#!/bin/sh

echo "Running A*"
for i in {0..15}; do
	timeout --kill-after 4100 3600 ./run.py -w 1 -q $i  $@
	sleep 300
done

echo "Running Dijstra"
for i in {0..15} ;do
	timeout --kill-after 4100 3600 ./run.py -w 0 -q $i  $@
	sleep 300
done
