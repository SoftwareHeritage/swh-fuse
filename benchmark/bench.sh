#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 CASE ATTEMPTS"
    echo "pick CASE in pythonSLOC, pythonFiles"
    exit 1
fi

CASE=$1
SWHID_NUM=$2
BASENAME="$CASE-${SWHID_NUM}times"

source ~/.pyenv/versions/swh/bin/activate
swh --log-config ~/.config/swh/global.yml fs mount -f /home/martin/mountpoint/ 2>&1 | tee -a "${BASENAME}_fuse.log" &

sleep 1

for swhid in `shuf -n $SWHID_NUM popular-python-releases-targetdirectories.csv`; do
    ./bench.py $CASE $swhid >> "$BASENAME.csv" 2>> "${BASENAME}_test.log"
done

kill %1
