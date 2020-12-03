#!/usr/bin/env python3

# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import json
from typing import Any, Dict

import requests

from swh.fuse.tests.api_url import (
    GRAPH_API_REQUEST,
    swhid_to_graph_url,
    swhid_to_web_url,
)
from swh.fuse.tests.data.config import ALL_ENTRIES, ORIGIN_URL, REV_SMALL_HISTORY
from swh.model.identifiers import (
    CONTENT,
    DIRECTORY,
    RELEASE,
    REVISION,
    SNAPSHOT,
    SWHID,
    parse_swhid,
)

API_URL_real = "https://archive.softwareheritage.org/api/1"
API_URL_test = "https://invalid-test-only.archive.softwareheritage.org/api/1"

MOCK_ARCHIVE: Dict[str, Any] = {}
# Temporary map (swhid -> metadata) to ease data generation
METADATA: Dict[SWHID, Any] = {}


def get_short_type(object_type: str) -> str:
    short_type = {
        CONTENT: "cnt",
        DIRECTORY: "dir",
        REVISION: "rev",
        RELEASE: "rel",
        SNAPSHOT: "snp",
    }
    return short_type[object_type]


def generate_archive_web_api(
    swhid: SWHID, raw: bool = False, recursive: bool = False
) -> None:
    # Already in mock archive
    if swhid in METADATA and not raw:
        return

    url = swhid_to_web_url(swhid, raw)

    if raw:
        data = requests.get(f"{API_URL_real}/{url}").text
    else:
        data = requests.get(f"{API_URL_real}/{url}").text
        data = json.loads(data)

    MOCK_ARCHIVE[url] = data
    METADATA[swhid] = data

    # Retrieve additional needed data for different artifacts (eg: content's
    # blob data, release target, etc.)
    if recursive:
        if swhid.object_type == CONTENT:
            generate_archive_web_api(swhid, raw=True)
        elif swhid.object_type == RELEASE:
            target_type = METADATA[swhid]["target_type"]
            target_id = METADATA[swhid]["target"]
            target = parse_swhid(f"swh:1:{get_short_type(target_type)}:{target_id}")
            generate_archive_web_api(target, recursive=True)


def generate_archive_graph_api(swhid: SWHID) -> None:
    if swhid.object_type == REVISION:
        # Empty history for all revisions (except REV_SMALL_HISTORY used in tests)
        url = swhid_to_graph_url(swhid, GRAPH_API_REQUEST.HISTORY)
        MOCK_ARCHIVE[url] = ""
        if str(swhid) == REV_SMALL_HISTORY:
            # TODO: temporary fix, retrieve from the graph API once it is public
            history = """
swh:1:rev:37426e42cf78a43779312d780eecb21a64006d99 swh:1:rev:0cf3c2ad935be699281ed20fb3d2f29554e6229b
swh:1:rev:0cf3c2ad935be699281ed20fb3d2f29554e6229b swh:1:rev:37180552769b316e7239d047008f187127e630e6
swh:1:rev:37180552769b316e7239d047008f187127e630e6 swh:1:rev:dd2716f56c7cf55f2904fbbf4dfabaab1afbcd88
swh:1:rev:dd2716f56c7cf55f2904fbbf4dfabaab1afbcd88 swh:1:rev:968ec145278d3d6562e4b5ec4006af97dc0da563
swh:1:rev:968ec145278d3d6562e4b5ec4006af97dc0da563 swh:1:rev:34dc7053ebfd440648f49dc83d2538ab5e7ceda5
swh:1:rev:34dc7053ebfd440648f49dc83d2538ab5e7ceda5 swh:1:rev:c56a729ff1d9467d612bf522614519ac7b97f798
swh:1:rev:c56a729ff1d9467d612bf522614519ac7b97f798 swh:1:rev:eb7807c4fe7a2c2ad3c074705fb70de5eae5abe3
swh:1:rev:eb7807c4fe7a2c2ad3c074705fb70de5eae5abe3 swh:1:rev:d601b357ecbb1fa33dc10c177bb557868be07deb
swh:1:rev:d601b357ecbb1fa33dc10c177bb557868be07deb swh:1:rev:2a2474d497ae19472b4366f6d8d62e9a516787c3
swh:1:rev:2a2474d497ae19472b4366f6d8d62e9a516787c3 swh:1:rev:eed5c0aa249f3e17bbabeeba1650ab699e3dff5a
swh:1:rev:eed5c0aa249f3e17bbabeeba1650ab699e3dff5a swh:1:rev:67d1f0a9aafaa7dcd63b86032127ab660e630c46
swh:1:rev:67d1f0a9aafaa7dcd63b86032127ab660e630c46 swh:1:rev:2e3fa5bd68677762c619d83dfdf1a83ba7f0e749
swh:1:rev:2e3fa5bd68677762c619d83dfdf1a83ba7f0e749 swh:1:rev:a9c639ec8af3a4099108788c1db0176c7fea5799
swh:1:rev:a9c639ec8af3a4099108788c1db0176c7fea5799 swh:1:rev:c06ea8f9445dbb5eda99ac8730d7fb2177df6816
swh:1:rev:c06ea8f9445dbb5eda99ac8730d7fb2177df6816 swh:1:rev:422b8a6be4aab120685f450db0a520fcb5a8aa6b
swh:1:rev:422b8a6be4aab120685f450db0a520fcb5a8aa6b swh:1:rev:e8759934711c70c50b5d616be22104e649abff58
swh:1:rev:e8759934711c70c50b5d616be22104e649abff58 swh:1:rev:63b5e18207c7f8a261c1f7f50fd8c7bbf9a21bda
swh:1:rev:63b5e18207c7f8a261c1f7f50fd8c7bbf9a21bda swh:1:rev:5dfe101e5197d6854aa1d8c9907ac7851468d468
swh:1:rev:5dfe101e5197d6854aa1d8c9907ac7851468d468 swh:1:rev:287d69ddacba3f5945b70695fb721b2f055d3ee6
swh:1:rev:287d69ddacba3f5945b70695fb721b2f055d3ee6 swh:1:rev:85a701c8f668fc03e6340682956e7ca7d9cf54bc
swh:1:rev:85a701c8f668fc03e6340682956e7ca7d9cf54bc swh:1:rev:241305caab232b04666704dc6853c41312cd283a
swh:1:rev:241305caab232b04666704dc6853c41312cd283a swh:1:rev:0d9565a4c144c07dab052161eb5fa3815dcd7f06
swh:1:rev:0d9565a4c144c07dab052161eb5fa3815dcd7f06 swh:1:rev:72c6c60d80cdfe63af5046a1a98549f0515734f2
swh:1:rev:72c6c60d80cdfe63af5046a1a98549f0515734f2 swh:1:rev:c483808e0ff9836bc1cda0ce95d77c8b7d3be91c
swh:1:rev:c483808e0ff9836bc1cda0ce95d77c8b7d3be91c swh:1:rev:1c60be2f32f70f9181a261ae2c2b4efe353d0f85
swh:1:rev:1c60be2f32f70f9181a261ae2c2b4efe353d0f85 swh:1:rev:bcf29b882acdf477be412fdb401b0fc2a6c819aa
swh:1:rev:bcf29b882acdf477be412fdb401b0fc2a6c819aa swh:1:rev:261d543920e1c66049c469773ca989aaf9ce480e
swh:1:rev:261d543920e1c66049c469773ca989aaf9ce480e swh:1:rev:24d5ff75c3abfe7b327c48468ed9a39f0d8a0427
swh:1:rev:24d5ff75c3abfe7b327c48468ed9a39f0d8a0427 swh:1:rev:d3c0762ff85ff7d29668d1f5d2361df03978bbea
swh:1:rev:d3c0762ff85ff7d29668d1f5d2361df03978bbea swh:1:rev:af44ec2856603b8a978a1f2582c285c7c0065403
swh:1:rev:af44ec2856603b8a978a1f2582c285c7c0065403 swh:1:rev:69a34503f4d51b639855501f1b6d6ce2da4e16c7
swh:1:rev:69a34503f4d51b639855501f1b6d6ce2da4e16c7 swh:1:rev:0364a801bb29211d4731f3f910c7629286b51c45
swh:1:rev:0364a801bb29211d4731f3f910c7629286b51c45 swh:1:rev:25eb1fd3c9d997e460dff3e03d87e398e616c726
swh:1:rev:25eb1fd3c9d997e460dff3e03d87e398e616c726 swh:1:rev:4a1f86ccd7e823f63d12208baef79b1e74479203
swh:1:rev:4a1f86ccd7e823f63d12208baef79b1e74479203 swh:1:rev:0016473117e4bc3c8959bf2fd49368844847d74c
swh:1:rev:0016473117e4bc3c8959bf2fd49368844847d74c swh:1:rev:935442babcf4f8ae52c1a13bb9ce07270a302886
swh:1:rev:935442babcf4f8ae52c1a13bb9ce07270a302886 swh:1:rev:1f3cff91f6762b0f47f41025b5e2c5ac942479ba
swh:1:rev:1f3cff91f6762b0f47f41025b5e2c5ac942479ba swh:1:rev:bc286c7f2ceb5c3d2e06ec72f78d28842f94ef65
swh:1:rev:bc286c7f2ceb5c3d2e06ec72f78d28842f94ef65 swh:1:rev:f038f4d533f897a29f9422510d1b3f0caac97388
swh:1:rev:f038f4d533f897a29f9422510d1b3f0caac97388 swh:1:rev:d6b7c96c3eb29b9244ece0c046d3f372ff432d04
swh:1:rev:d6b7c96c3eb29b9244ece0c046d3f372ff432d04 swh:1:rev:c01efc669f09508b55eced32d3c88702578a7c3e
"""  # NoQA: E501
            MOCK_ARCHIVE[url] = history

            hist_nodes = set(
                map(
                    parse_swhid,
                    [edge.split(" ")[1] for edge in history.strip().split("\n")],
                )
            )
            for swhid in hist_nodes:
                generate_archive_web_api(swhid, recursive=False)


def generate_origin_archive_web_api(url: str):
    url_visits = f"origin/{url}/visits/"
    data = requests.get(f"{API_URL_real}/{url_visits}").text
    data = json.loads(data)
    MOCK_ARCHIVE[url_visits] = data
    # Necessary since swh-fuse will check the origin URL using the get/ endpoint
    url_get = f"origin/{url}/get/"
    MOCK_ARCHIVE[url_get] = ""


for entry in ALL_ENTRIES:
    swhid = parse_swhid(entry)
    generate_archive_web_api(swhid, recursive=True)
    generate_archive_graph_api(swhid)

# Origin artifacts are not identified by SWHID but using an URL
generate_origin_archive_web_api(ORIGIN_URL)

print("# GENERATED FILE, DO NOT EDIT.")
print("# Run './gen-api-data.py > api_data.py' instead.")
print("# flake8: noqa")
print("from typing import Any, Dict")
print("")
print(f"API_URL = '{API_URL_test}'\n")
print(f"MOCK_ARCHIVE: Dict[str, Any] = {MOCK_ARCHIVE}")
