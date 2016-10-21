#!/usr/bin/env fish

# Setup
# =====
set timeLimit 620
set timeGiven 660
set killTime  700

set -l queries   4 8 9 10 12 14 15
set -l poolSizes 1 3 5 10 20 40 80
set -l algorithms "AStar" "Dijkstra" "DFS"
set -l weights   1



# Run experiments
# ===============

# Move old data in bench/last/  to  bench/old/
echo mkdir -p bench/old
mkdir -p bench/old
mv bench/last/* bench/old/


set benchDir "bench/"(date -Iseconds)

for p in $poolSizes
	for q in $queries
		for w in $weights
			for a in $algorithms
				timeout --kill-after $killTime $timeGiven  ./run.py --time $timeLimit  --alg=$a -w $w -q $q --pool-size $p $argv
			end
		end
	end
end

# Move all the output to the new directory
mv bench/last/ $benchDir



# Run analysis
# ============
if xset -q > /dev/null ^ /dev/null;  and ./analyze.fish $benchDir/*/*/*
  echo "Graphs ready"
else
  echo "Please run ./analyze.fish $benchDir/*/*/*"
end
