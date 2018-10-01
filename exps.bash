#!/usr/bin/env bash

# Setup
# =====
timeLimit=600
timeGiven=610
killTime=620


#queries=(10 11 12 13 14 15 16 17  20 21 22 23 24 25  30 31 32) # All queries
#queries=(10 11 12 13 14           20    22 23 24     30    32) # Selected queries
queries=(10 11 12 13 14)

#poolSizes=(1 10 20 40)
poolSizes=(40)

#set -l algorithms "AStar" "Dijkstra" "DFS"
algorithms=("AStar")

weights=(1)



# Run experiments
# ===============

# Move old data in bench/last/  to  bench/old/
echo mkdir -p bench/old
mkdir -p bench/old
mv bench/last/* bench/old/


benchDir="bench/$hostname_$(date -Iseconds)"

for p in $poolSizes; do
	for q in $queries; do
		for w in $weights; do
			for a in $algorithms; do
				notify-send -t 2000 "Running q$q k=$p $a"
				timeout --kill-after $killTime $timeGiven  ./run.py --time $timeLimit  --alg=$a -w $w -q $q --pool-size $p $argv
			done
		done
	done
done

# Move all the output to the new directory
mv bench/last/ $benchDir


echo
echo "Generating graphs..."

# Run analysis
# ============
if ./analyze.bash $benchDir; then
  echo "Graphs ready"

  if [[ $DISPLAY ]] && [[ $IN_NIX_SHELL -ne "pure" ]]; then
	  xdg-open "$benchDir"
  else
    echo "Graphs can't be shown on this environment :("
  fi
else
  echo "Please run ./analyze.bash $benchDir/*/*/*"
fi
