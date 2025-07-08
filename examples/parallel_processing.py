#!/usr/bin/env python

"""
Example program trying to search in parallel over 1000 swh:dir entries. It creates
as many worker sub-processes as required, and spawn a temporary mountpoint for each
dir entry.
"""

from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from subprocess import DEVNULL, run
from time import perf_counter

import click

from swh.fuse.fuse import SwhFuseTmpMount

DIRLIST = "concatenated_dir_ids.bin"


def process_wrapper(swhdir: str):
    with SwhFuseTmpMount() as mountpoint:
        path = str(mountpoint) + swhdir
        run(
            # grep would be a kind of stress test for swhfuse
            # ["grep", "-r", "something", path],
            ["find", path, "-iname", "*.py"],
            stderr=DEVNULL,
            stdout=DEVNULL,
        )
        print(datetime.now().isoformat(), "done", swhdir)


def gen_paths():
    with open(DIRLIST, "rb") as dirfile:
        while dirid := dirfile.read(20):
            yield "/archive/swh:1:dir:" + dirid.hex()


@click.command()
@click.argument("workers_n", type=int, default=1)
def main(workers_n: int):
    f"""
    Launch WORKERS_N sub-process in parallel, to process a dir list (SWH dir 20-bytes
    IDs, concatenated in {DIRLIST}).
    For each dir, this mounts one instance of swh-fuse for the worker process.

    HINT: if you are not authorized to FUSE-mount on your machine, wrap this script
    in a namespace:

        unshare --pid --kill-child --user --map-root-user --mount ./parallel_processing.py 4
    """
    global_start = perf_counter()
    print(datetime.now().isoformat(), "starting")

    with ProcessPoolExecutor(max_workers=workers_n) as executor:
        results = executor.map(process_wrapper, gen_paths())
        for _ in results:
            pass

    print(
        datetime.now().isoformat(),
        "Done in %.2f seconds" % (perf_counter() - global_start),
    )


if __name__ == "__main__":
    main()
