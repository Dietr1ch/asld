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


echo "Building logs"
for i in {0..15} ;do
	jq -S '. | {query: .query, weight: .weight, paths: .data.PathCount, params: .params, lastHist: .data.StatsHistory[-1]}' last-q$i-w0--p40--time1800--ans1000--triples100000.json > cmp-$i.log
	jq -S '. | {query: .query, weight: .weight, paths: .data.PathCount, params: .params, lastHist: .data.StatsHistory[-1]}' last-q$i-w1--p40--time1800--ans1000--triples100000.json >> cmp-$i.log
done
