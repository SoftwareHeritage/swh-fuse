#!/usr/bin/env python3

# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

import requests

API_URL_real = "https://archive.softwareheritage.org/api/1"
API_URL_test = "https://invalid-test-only.archive.softwareheritage.org/api/1"

# Use the Linux kernel as a testing repository
ROOT_HASH = "9eb62ef7dd283f7385e7d31af6344d9feedd25de"
README_HASH = "669ac7c32292798644b21dbb5a0dc657125f444d"

ROOT_SWHID = f"swh:1:dir:{ROOT_HASH}"

urls = {
    "ROOT": f"directory/{ROOT_HASH}/",
    "README": f"content/sha1_git:{README_HASH}/",
    "README_RAW": f"content/sha1_git:{README_HASH}/raw/",
}

print("# GENERATED FILE, DO NOT EDIT.")
print("# Run './gen-api-data.py > api_data.py' instead.")
print("# fmt: off")

print("")
print(f"API_URL = '{API_URL_test}'")
print(f"ROOT_SWHID = '{ROOT_SWHID}'")
for name, url in urls.items():
    print(f"{name}_URL = '{url}'")
print("")

print("MOCK_ARCHIVE = {")
for url in urls.values():
    print(f"    '{url}':  # NoQA: E501")
    print('    r"""', end="")

    data = requests.get(f"{API_URL_real}/{url}").text
    if url.endswith("/raw/"):
        print(data, end="")
    else:
        parsed = json.loads(data)
        print(json.dumps(parsed, indent=2, sort_keys=True))

    print('""",  # NoQA: E501')
print("}")
