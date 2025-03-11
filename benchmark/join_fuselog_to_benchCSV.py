#!/usr/bin/env python
import logging
import os
from typing import Tuple
from datetime import datetime
from pathlib import Path
from time import perf_counter, sleep
from sys import argv
from tempfile import TemporaryDirectory
from subprocess import run
from dataclasses import dataclass
import re

import click
import requests
import yaml

float_re = re.compile(r"[-+]?\d*\.\d+|\d+")


@dataclass
class FuseMeasure:
    waiting_graph: float = 0
    waiting_storage: float = 0
    waiting_objstorage: float = 0

def parse_float(s):
    try:
        m = float_re.search(s)
        if m:
            return float(m.group())
        return float(s)
    except ValueError as e:
        return 0.

def parse_fuse_log(filename):
    measure = FuseMeasure()
    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines[-10:]:
            if "waiting for graph backend" in line:
                measure.waiting_graph = parse_float(line)
            elif "waiting for storage backend" in line:
                measure.waiting_storage = parse_float(line)
            elif "waiting for objstorage backend" in line:
                measure.waiting_objstorage = parse_float(line)
    return measure


@click.command()
@click.argument("csv_path")
@click.argument("logfiles", nargs=-1)
def main(csv_path: str, logfiles: tuple[str, ...]):
    """
    join given CSV with FUSE logs - we expect each FUSE log filename to be like::

        *_swh_1_dir_1234567874635241345754*


    and to terminate like::

        INFO:swh.fuse:Spent 0.000000 seconds waiting for graph backend
        INFO:swh.fuse:Spent 0.000000 seconds waiting for storage backend
        INFO:swh.fuse:Spent 0.000000 seconds waiting for objstorage backend

    """
    measures = {}
    for logfile in logfiles:
        measure = parse_fuse_log(logfile)
        swh_i = logfile.index("swh")
        swhid = logfile[swh_i:swh_i+50].replace('_', ':')
        measures[swhid] = f"{measure.waiting_graph},{measure.waiting_storage},{measure.waiting_objstorage}"

    with open(csv_path) as f:
        for l in f:
            line = l.strip()
            splitted = line.split(",")
            swhid = splitted[1]
            if swhid in measures:
                print(f"{line},{measures[swhid]}")
            else:
                print(f"{line},-1111111,-1111111,-1111111")


if __name__ == "__main__":
    main()
