#!/bin/bash

if [ $# -le 2 ]; then
    echo "Usage: $0 CASE ATTEMPTS [swhid_list.txt]"
    echo "pick CASE in pythonSLOC, pythonFiles, scancode, hyply"
    exit 1
fi

CASE=$1
SWHID_NUM=$2
SWHID_LIST=${3:-$HOME/targetdirectories.csv}
BASENAME="$CASE-${SWHID_NUM}times"

source ~/venvs/fuse/bin/activate

sleep 1

for swhid in `shuf -n $SWHID_NUM $SWHID_LIST`; do
    num=${swhid//:/_}
    swh fs mount -f ~/mountpoint/ >> "${BASENAME}_${num}fuse.log" 2>&1 &
    sleep 1
    ../bench.py $CASE "$swhid" >> "$BASENAME.csv" 2>> "${BASENAME}_${num}test.log"
    kill %1
    sleep 3
    umount /home/martin/mountpoint
    sleep 3
done

