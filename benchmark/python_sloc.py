#!/usr/bin/env python
from pathlib import Path
from time import perf_counter, sleep
from sys import argv
from tempfile import TemporaryDirectory
from subprocess import run

import requests

def count_sloc_fs(directory:Path) -> int:
    pysloc = 0

    for f in directory.glob("**/*.py"):
        with open(f) as fp:
            pysloc += sum(1 for line in fp)

    return pysloc

def count_sloc_tarball(swhid:str) -> int:
    pysloc = 0
    cooker_url = f"https://archive.softwareheritage.org/api/1/vault/flat/{swhid}"
    # TODO add bearer token

    with TemporaryDirectory() as tmpdir:
        response = requests.post(cooker_url)
        print(f"POST /flat got {response.status_code}")
        response.raise_for_status()

        while True:
            response = requests.get(cooker_url)
            response.raise_for_status()
            obj = response.json()
            if obj['status'] == 'done':
                print(obj)
                break
            else:
                print(f"{obj['id']} is {obj['status']} {obj['progress_message']}")
                sleep(5)

        response = requests.get(obj['fetch_url'])
        tarball = f"{tmpdir}/{obj['id']}.tag.gz"
        with open(tarball, 'wb') as f:
            f.write(response.content)
        run(["tar", "-xzf", tarball, "-C", tmpdir])
        Path(tarball).unlink()
        untarred = Path(tmpdir) / obj["swhid"]
        pysloc = count_sloc_fs(untarred)

    return pysloc



def python_sloc(swhid):
    """
    Benchmarks swh-fuse against tarball download when estimating Python SLOCs in given swhid (expected to be a revision ID).
    """
    directory = Path(f"/home/martin/mountpoint/archive/{swhid}")
    start = perf_counter()
    sloc = count_sloc_fs(directory)
    end = perf_counter()
    print(f"Old fuse took {end-start} seconds to count {sloc} lines")

    start = perf_counter()
    sloc = count_sloc_tarball(swhid)
    end = perf_counter()
    print(f"Tarball took {end-start} seconds to count {sloc} lines")


if __name__ == '__main__':
    python_sloc(argv[1])