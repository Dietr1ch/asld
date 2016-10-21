#!/usr/bin/env fish

for d in $argv
  echo
  echo "Analyzing '$d'..."
  ./cmp.py $d/*.json   --no-show --data memory      --x goals_found --first-goals 1 5 10 20 50 100 200 500 1000 > $d/log.txt
  ./cmp.py $d/*.json   --no-show --data memory
  ./cmp.py $d/*.json   --no-show --data memory      --x wallClock

  ./cmp.py $d/*.json   --no-show --data goals_found
  ./cmp.py $d/*.json   --no-show --data goals_found --x wallClock

  ./cmp.py $d/*.json   --no-show --data expansions
  ./cmp.py $d/*.json   --no-show --data expansions  --x wallClock
end
