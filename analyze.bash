#!/usr/bin/env bash

for d in ${BASH_ARGV[*]}; do
  echo
  echo "Analyzing '$d'..."
  ./utils/load_dump.py $d --x remote_expansions goals_found wallClock memory  --y goals_found remote_expansions wallClock memory
  #./cmp.py $d/*.json   --no-show --data memory      --x goals_found --first-goals 1 5 10 20 50 100 200 500 1000 > $d/log.txt
  #./cmp.py $d/*.json   --no-show --data memory
  #./cmp.py $d/*.json   --no-show --data memory      --x wallClock

  #./cmp.py $d/*.json   --no-show --data goals_found
  #./cmp.py $d/*.json   --no-show --data goals_found --x wallClock

  #./cmp.py $d/*.json   --no-show --data expansions  --x wallClock
done
