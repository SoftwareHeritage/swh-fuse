#!/usr/bin/env python3

# Copyright (C) 2020-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import json
from typing import Any, Dict

import requests

from swh.fuse.tests.web_api.api_url import swhid_to_history_url, swhid_to_web_url
from swh.fuse.tests.web_api.data.config import (
    ALL_ENTRIES,
    FAKE_SNP_SPECIAL_CASES,
    FAKE_SNP_SPECIAL_CASES_SWHID,
    ORIGIN_URL,
    REV_SMALL_HISTORY,
)
from swh.model.hashutil import hash_to_bytes
from swh.model.swhids import CoreSWHID, ObjectType

API_URL_real = "https://archive.softwareheritage.org/api/1"
API_URL_test = "https://invalid-test-only.archive.softwareheritage.org/api/1"

# Use your own API token to lift rate limiting. Note: this is not necessary to generate
# the API data only once but can be useful when re-generating it multiple times.
API_TOKEN = ""


MOCK_ARCHIVE: Dict[str, Any] = {}
# Temporary map (swhid -> metadata) to ease data generation
METADATA: Dict[CoreSWHID, Any] = {}


def get_from_api(endpoint: str) -> str:
    headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
    result = requests.get(f"{API_URL_real}/{endpoint}", headers=headers)
    if result.status_code != 200:
        raise RuntimeError(f"API request failed: {result.status_code} {result.text}")
    return result.text


def generate_archive_web_api(
    swhid: CoreSWHID, raw: bool = False, recursive: bool = False
) -> None:
    # Already in mock archive
    if swhid in METADATA and not raw:
        return

    url = swhid_to_web_url(swhid, raw)

    data = get_from_api(url)
    if not raw:
        data = json.loads(data)

    MOCK_ARCHIVE[url] = data
    METADATA[swhid] = data

    # Retrieve additional needed data for different artifacts (eg: content's
    # blob data, release target, etc.)
    if recursive:
        if swhid.object_type == ObjectType.CONTENT:
            generate_archive_web_api(swhid, raw=True)
        elif swhid.object_type == ObjectType.RELEASE:
            try:
                target_type = METADATA[swhid]["target_type"]
                target_id = METADATA[swhid]["target"]
            except KeyError:
                print(f"keyerror on METADATA[{swhid}]={METADATA[swhid]}")
            target = CoreSWHID(
                object_type=ObjectType[target_type.upper()],
                object_id=hash_to_bytes(target_id),
            )
            generate_archive_web_api(target, recursive=True)


def generate_archive_graph_api(swhid: CoreSWHID) -> None:
    if swhid.object_type == ObjectType.REVISION:
        # Empty history for all revisions (except REV_SMALL_HISTORY used in tests)
        url = swhid_to_history_url(swhid)
        MOCK_ARCHIVE[url] = "[]"
        if str(swhid) == REV_SMALL_HISTORY:
            history = json.loads(get_from_api(url))
            MOCK_ARCHIVE[url] = history
            revs = set(CoreSWHID.from_string("swh:1:rev:" + e["id"]) for e in history)
            for swhid in revs:
                generate_archive_web_api(swhid, recursive=False)


def generate_origin_archive_web_api(url: str):
    url_visits = f"origin/{url}/visits/"
    data = get_from_api(url_visits)
    data = json.loads(data)
    MOCK_ARCHIVE[url_visits] = data
    # Necessary since swh-fuse will check the origin URL using the get/ endpoint
    url_get = f"origin/{url}/get/"
    MOCK_ARCHIVE[url_get] = ""


if __name__ == "__main__":
    for entry in ALL_ENTRIES:
        swhid = CoreSWHID.from_string(entry)
        generate_archive_web_api(swhid, recursive=True)
        generate_archive_graph_api(swhid)

    # Custom fake snapshot to handle most special cases
    MOCK_ARCHIVE[swhid_to_web_url(FAKE_SNP_SPECIAL_CASES_SWHID)] = {
        "branches": FAKE_SNP_SPECIAL_CASES
    }

    # Origin artifacts are not identified by SWHID but using an URL
    generate_origin_archive_web_api(ORIGIN_URL)

    print("# GENERATED FILE, DO NOT EDIT.")
    print("# Run './gen-api-data.py > api_data.py' instead.")
    print("# flake8: noqa")
    print("from typing import Any, Dict")
    print("")
    print(f"API_URL = '{API_URL_test}'\n")
    print(f"MOCK_ARCHIVE: Dict[str, Any] = {MOCK_ARCHIVE}")
