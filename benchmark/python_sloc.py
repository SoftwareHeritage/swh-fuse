#!/usr/bin/env python
from typing import Tuple
from datetime import datetime
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

def download_vault(swhid:str) -> Tuple[TemporaryDirectory, Path]:
    vault_url = f"https://archive.softwareheritage.org/api/1/vault/flat/{swhid}"
    # TODO add bearer token

    tmpdir = TemporaryDirectory()
    dirpath = tmpdir.name
    response = requests.post(vault_url)
    response.raise_for_status()

    while True:
        response = requests.get(vault_url)
        response.raise_for_status()
        obj = response.json()
        if obj["status"] == "done":
            break
        else:
            sleep(2)

    response = requests.get(obj["fetch_url"])
    tarball = f"{dirpath}/{obj['id']}.tag.gz"
    with open(tarball, "wb") as f:
        f.write(response.content)
    run(["tar", "-xzf", tarball, "-C", dirpath])
    Path(tarball).unlink()
    untarred = Path(dirpath) / obj["swhid"]
    return (tmpdir, untarred)

def python_sloc(swhid):
    """
    Benchmarks swh-fuse against tarball download when estimating Python SLOCs in given
    swhid (expected to be a revision ID).
    We start by downloading from the vault, to let `swh fs mount` finish its mount in
    the background.
    """
    start_dt = datetime.now().isoformat(timespec='seconds')

    start_dl = perf_counter()
    tmpdir, untarred = download_vault(swhid)
    start_count = perf_counter()
    res_vault = count_sloc_fs(untarred)
    end = perf_counter()
    time_vault_total = end - start_dl
    time_baseline = end - start_count
    tmpdir.cleanup()

    fuse_folder = Path(f"/home/martin/mountpoint/archive/{swhid}")

    start = perf_counter()
    res_fuse_cold = count_sloc_fs(fuse_folder)
    end = perf_counter()
    time_fuse_cold = end-start

    start = perf_counter()
    res_fuse_hot = count_sloc_fs(fuse_folder)
    end = perf_counter()
    time_fuse_hot = end - start

    print(f"{start_dt},{swhid},"\
          f"{time_fuse_cold},{time_fuse_hot},{time_vault_total},{time_baseline},"\
          f"{res_fuse_cold},{res_fuse_hot},{res_vault}")

if __name__ == '__main__':
    for swhid in argv[1:]:
        python_sloc(swhid)