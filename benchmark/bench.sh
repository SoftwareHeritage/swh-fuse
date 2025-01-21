#!/bin/bash

BASENAME="pythonsloc-test"

SWHID_NUM=10
CSV="$BASENAME.csv"
LOG="$BASENAME.log"

source ~/.pyenv/versions/swh/bin/activate
swh fs clean
swh --log-config ~/.config/swh/global.yml fs mount -f /home/martin/mountpoint/ 2>&1 | tee $LOG &

sleep 1

for $swhid in `shuf -n $SWHID_NUM popular-python-releases-targetdirectories.csv`; do
    ./python_sloc.py $swhid >> $CSV
done

kill %1
