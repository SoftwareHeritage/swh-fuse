#!/usr/bin/env python3

# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import json
from typing import Any, Dict

import requests

from swh.fuse.tests.data.config import ALL_ENTRIES
from swh.model.identifiers import CONTENT, DIRECTORY, REVISION, SWHID, parse_swhid

API_URL_real = "https://archive.softwareheritage.org/api/1"
API_URL_test = "https://invalid-test-only.archive.softwareheritage.org/api/1"

SWHID2URL: Dict[str, str] = {}
MOCK_ARCHIVE: Dict[str, Any] = {}
# Temporary map (swhid -> metadata) to ease data generation
METADATA: Dict[SWHID, Any] = {}


def swhid2url(swhid: SWHID) -> str:
    prefix = {
        CONTENT: "content/sha1_git:",
        DIRECTORY: "directory/",
        REVISION: "revision/",
    }

    return f"{prefix[swhid.object_type]}{swhid.object_id}/"


def generate_archive_data(swhid: SWHID, raw: bool = False) -> None:
    url = swhid2url(swhid)
    SWHID2URL[str(swhid)] = url

    if raw:
        url += "raw/"
        data = requests.get(f"{API_URL_real}/{url}").text
    else:
        data = requests.get(f"{API_URL_real}/{url}").text
        data = json.loads(data)

    MOCK_ARCHIVE[url] = data
    METADATA[swhid] = data


for entry in ALL_ENTRIES:
    swhid = parse_swhid(entry)
    generate_archive_data(swhid)

    # Retrieve raw blob data for content artifact
    if swhid.object_type == CONTENT:
        generate_archive_data(swhid, raw=True)
    # Retrieve parent commits for revision artifact
    elif swhid.object_type == REVISION:
        for parent in METADATA[swhid]["parents"]:
            parent_swhid = parse_swhid(f"swh:1:rev:{parent['id']}")
            generate_archive_data(parent_swhid)

print("# GENERATED FILE, DO NOT EDIT.")
print("# Run './gen-api-data.py > api_data.py' instead.")
print("# flake8: noqa")
print("")
print(f"API_URL = '{API_URL_test}'\n")
print(f"SWHID2URL = {SWHID2URL}\n")
print(f"MOCK_ARCHIVE = {MOCK_ARCHIVE}")
