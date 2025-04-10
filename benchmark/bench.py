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

import click
import requests
import yaml



def python_sloc(directory: Path, output:str) -> int:
    pysloc = 0
    for f in directory.glob("**/*.py"):
        with open(f) as fp:
            pysloc += sum(1 for line in fp)

    return pysloc


def python_files(directory: Path, output: str) -> int:
    nbfiles = 0
    for f in directory.glob("**/*.py"):
        nbfiles += 1
    return nbfiles


def scancode(directory: Path, output: str) -> int:
    run(["scancode", "-clpieu", "--json-pp", output, directory.absolute()])
    return 0

def hyply(directory: Path, output: str) -> int:
    res = run(["hyply", directory.absolute()], capture_output=True, text=True)
    lines = res.stdout.split("\n")
    with open(output, 'w') as output_f:
        output_f.write(res.stdout)
    try:
        return lines[0]
    except IndexError:
        return -1

class Runner:

    def __init__(self):
        conf_path = os.path.join(click.get_app_dir("swh"), "global.yml")
        conf = yaml.load(open(conf_path), Loader=yaml.FullLoader)
        try:
            token = conf["swh"]["fuse"]["web-api"]["auth-token"]
        except KeyError:
            logging.warning("No auth token found in %s", conf_path)
            token = None
        self.token = token


    def download_vault(self, swhid: str) -> Tuple[TemporaryDirectory, Path]:
        vault_url = f"https://archive.softwareheritage.org/api/1/vault/flat/{swhid}"
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        response = requests.post(vault_url, headers=headers)
        try:
            response.raise_for_status()
        except:
            logging.warning("POST /vault failed: %s", response.text)
            sleep(3)

        while True:
            response = requests.get(vault_url, headers=headers)
            response.raise_for_status()
            obj = response.json()
            if obj["status"] == "done":
                break
            else:
                sleep(2)

        response = requests.get(obj["fetch_url"], headers=headers)

        tmpdir = TemporaryDirectory(dir="/data/martin/tmp")
        dirpath = tmpdir.name
        tarball = f"{dirpath}/{obj['id']}.tag.gz"
        with open(tarball, "wb") as f:
            f.write(response.content)
        run(["tar", "-xzf", tarball, "-C", dirpath])
        Path(tarball).unlink()
        untarred = Path(dirpath) / obj["swhid"]
        return (tmpdir, untarred)


    def testrun(self, case_function, swhid):
        """
        Benchmarks swh-fuse against tarball download for given case and given
        swhid (expected to be a revision ID).
        We start by downloading from the vault, to let `swh fs mount` finish its mount in
        the background... also because the vault returns an error almost half of the time.
        """
        outputbasename = swhid.replace(":", "_")
        start_dt = datetime.now().isoformat(timespec="seconds")

        start_dl = perf_counter()
        tmpdir, untarred = self.download_vault(swhid)
        try:
            start_count = perf_counter()
            res_vault = case_function(untarred, f"{outputbasename}_vault.json")
            end = perf_counter()
            time_vault_total = end - start_dl
            time_baseline = end - start_count
        finally:
            tmpdir.cleanup()

        fuse_folder = Path(f"/home/martin/mountpoint/archive/{swhid}")

        start = perf_counter()
        res_fuse_cold = case_function(fuse_folder, f"{outputbasename}_fusecold.json")
        end = perf_counter()
        time_fuse_cold = end - start

        start = perf_counter()
        res_fuse_hot = case_function(fuse_folder, f"{outputbasename}_fusehot.json")
        end = perf_counter()
        time_fuse_hot = end - start

        print(
            f"{start_dt},{swhid},"
            f"{time_fuse_cold},{time_fuse_hot},{time_vault_total},{time_baseline},"
            f"{res_fuse_cold},{res_fuse_hot},{res_vault}"
        )

@click.command()
@click.argument("case")
@click.argument("swhids", nargs=-1)
def main(case:str, swhids: tuple[str, ...]):
    """
    Do one performance measure. Will print one CSV line per SWHID.

    Valid case names are: PythonSLOC, PythonFiles
    """
    match argv[1].lower():
        case "pythonsloc":
            case_function = python_sloc
        case "pythonfiles":
            case_function = python_files
        case "scancode":
            case_function = scancode
        case "hyply":
            case_function = hyply

    runner = Runner()
    for swhid in argv[2:]:
        runner.testrun(case_function, swhid)


if __name__ == "__main__":
    main()
