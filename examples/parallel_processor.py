#!/usr/bin/env python

"""
Launch WORKERS_N sub-process in parallel, to count *.py files in a dir list (SWH dir
20-bytes IDs, concatenated in concatenated_dir_ids.bin).
For each dir, this mounts one instance of swh-fuse over a temporary mountpoint.

If you are not authorized to FUSE-mount on your machine, wrap this script in a
namespace:

    unshare --pid --kill-child --user --map-root-user --mount ./parallel_processor.py 4
"""

from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from time import perf_counter

import click

from swh.fuse.fuse import SwhFsTmpMount

DIRLIST = "concatenated_dir_ids.bin"


def count_py_worker(swhdir: Path) -> int:
    nbfiles = 0
    with SwhFsTmpMount() as mountpoint:
        path = mountpoint / swhdir
        for f in path.glob("**/*.py"):
            nbfiles += 1
    print(datetime.now().isoformat(), f"Found {nbfiles} .py files in {swhdir}")
    return nbfiles


def gen_paths():
    """
    Generates paths to each directory SWHID we'd like to analyze, relative to an
    SwhFS mountpoint.
    """
    with open(DIRLIST, "rb") as dirfile:
        while dirid := dirfile.read(20):
            yield Path("archive") / Path("swh:1:dir:" + dirid.hex())


@click.command(help=__doc__)
@click.argument("workers_n", type=int)
def main(workers_n: int):
    global_start = perf_counter()
    print(datetime.now().isoformat(), "starting")

    with SwhFsTmpMount():
        # some python imports are made only when mounting, so we mount once to
        # indirectly trigger those imports. This ensure that processes forked next
        # by ProcessPoolExecutor will be fully loaded.
        pass

    total_py = 0
    with ProcessPoolExecutor(max_workers=workers_n) as executor:
        results = executor.map(count_py_worker, gen_paths())
        for counter in results:
            total_py += counter

    print(
        datetime.now().isoformat(),
        f"Found {total_py} .py files in {(perf_counter() - global_start):.2f} seconds",
    )


if __name__ == "__main__":
    main()
