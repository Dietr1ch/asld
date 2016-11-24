#!/usr/bin/env fish

# Setup
# =====
set timeLimit 600
set timeGiven 610
set killTime  620


#set -l queries  10 11 12 13 14 15  20 21 22 23 24 25  30 31 32  # All queries
set -l queries  10 11    13 14     20    22 23 24     30    32  # Selected queries
#set -l queries  30  # TODO

set -l poolSizes 1 10 20 40
#set -l poolSizes 1

set -l algorithms "AStar" "Dijkstra" "DFS"
#set -l algorithms "AStar"

set -l weights   1



# Run experiments
# ===============

# Move old data in bench/last/  to  bench/old/
echo mkdir -p bench/old
mkdir -p bench/old
mv bench/last/* bench/old/


set benchDir "bench/"(hostname)"-"(date -Iseconds)

for p in $poolSizes
	for q in $queries
		for w in $weights
			for a in $algorithms
				notify-send -t 2000 "Running q$q k=$p $a"
				timeout --kill-after $killTime $timeGiven  ./run.py --time $timeLimit  --alg=$a -w $w -q $q --pool-size $p $argv
			end
		end
	end
end

# Move all the output to the new directory
mv bench/last/ $benchDir



# Run analysis
# ============
if xset -q > /dev/null ^ /dev/null;  and  ./analyze.fish $benchDir
	echo "Graphs ready"
	xdg-open "$benchDir"
else
  echo "Please run ./analyze.fish $benchDir/*/*/*"
end
