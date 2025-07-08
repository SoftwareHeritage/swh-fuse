#!/usr/bin/env python

"""
SWH-fuse stress test !
"""
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from subprocess import run, DEVNULL
from time import perf_counter

import click


DIRLIST = 'concatenated_dir_ids.bin'

def process_wrapper(folder):

    path = Path(mountpoint) / "archive" / ()
    run(
        ["grep", "-r", "the", str(path)],
        # ["find", str(path), "-iname", "*.py"],
        stderr=DEVNULL,
        stdout=DEVNULL,
    )
    print(datetime.now().isoformat(), "done", folder)
    return folder

def gen_paths():
    with open(DIRLIST, 'rb') as dirfile:
        while (dirid := dirfile.read(20)):
            yield "archive/swh:1:dir:" + dirid.hex()


@click.command()
@click.argument("workers_n", type=int, default=1)
def main(workers_n:int):
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

    print(datetime.now().isoformat(), "Done in %.2f seconds" % (perf_counter() - global_start))


if __name__ == "__main__":
    main()
