#!/bin/zsh

for d in $@; do
		./cmp.py $d/*.json   --no-show --data memory --x goalsFound --first-goals 1 5 10 20 50 100 200 500 1000 > $d/log.txt
		./cmp.py $d/*.json   --no-show --data goalsFound
done

