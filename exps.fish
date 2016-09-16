#!/usr/bin/env fish

# Setup
# =====
set timeLimit 3600
set timeGiven 3700
set killTime  3800

set -l weights   1 0
set -l queries   4 8 9 10 12 14 15
set -l poolSizes 5 10 20 40 80



# Run experiments
# ===============

# Move old data in bench/last/  to  bench/old/
mkdir -p bench/old
mv bench/last/* bench/old/;  or  exit

# Create new directory to hold results
set benchDir "bench/"(date -Iseconds)"/"
mkdir -p  $benchDir

for w in $weights
	for p in $poolSizes
		for q in $queries
			timeout --kill-after $killTime $timeGiven  ./run.py --time $timeLimit  -w $w -q $q --pool-size $p $argv
		end
	end
end

# Move all the output to the new directory
mv bench/last/ $benchDir



# Run analysis
# ============
#                bench/E/q/p/s
./analyze.fish $benchDir/*/*/*
