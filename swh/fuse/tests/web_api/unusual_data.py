"""
This module provides mock data like ``data.api_data``, but only to simulate graph's edge
cases, in particular missing dates that might interfere with ``by-date`` folders.

This might be replaced by proper graph tests. cf. https://gitlab.softwareheritage.org/swh/devel/swh-graph/-/issues/4844
"""

# flake8: noqa

import json
from typing import Any, Dict

API_URL = "https://invalid-test-only.archive.softwareheritage.org/api/1"

BROKEN_RELEASE_SWHID = "swh:1:rel:3333333333333333333333333333333333333333"
REVISION_SWHID = "swh:1:rev:2222222222222222222222222222222222222222"
BROKEN_REVISION_SWHID = "swh:1:rev:1111111111111111111111111111111111111111"

MOCK_ARCHIVE: Dict[str, Any] = {
    "release/3333333333333333333333333333333333333333/": json.dumps(
        {
            "name": "0.42.0",
            "message": "What if date is missing ?",
            "target": "2222222222222222222222222222222222222222",
            "target_type": "revision",
            "synthetic": False,
            "author": {
                "name": "Martin Kirchgessner",
            },
            "date": None,
            "id": "3333333333333333333333333333333333333333",
            "target_url": "https://archive.softwareheritage.org/api/1/revision/2222222222222222222222222222222222222222/",
        }
    ),
    # ref 2222 is OK, but 1111's date is missing
    "graph/visit/edges/swh:1:rev:2222222222222222222222222222222222222222": "\nswh:1:rev:2222222222222222222222222222222222222222 swh:1:rev:1111111111111111111111111111111111111111\n",
    "revision/2222222222222222222222222222222222222222/": json.dumps(
        {
            "message": "We're missing authors, but swhfuse should let it go",
            "date": "2020-03-09T22:09:51+00:00",
            "committer_date": "2020-03-09T22:09:51+00:00",
            "type": "git",
            "directory": "c6dcbe9711ea6d5a31429a833a3d0c59cbbb2578",
            "synthetic": False,
            "metadata": {},
            "parents": [
                {
                    "id": "1111111111111111111111111111111111111111",
                    "url": "https://archive.softwareheritage.org/api/1/revision/1111111111111111111111111111111111111111/",
                },
            ],
            "id": "2222222222222222222222222222222222222222",
            "extra_headers": [],
            "url": "https://archive.softwareheritage.org/api/1/revision/2222222222222222222222222222222222222222/",
            "history_url": "https://archive.softwareheritage.org/api/1/revision/2222222222222222222222222222222222222222/log/",
        }
    ),
    "revision/1111111111111111111111111111111111111111/": json.dumps(
        {
            "message": "An initial revision with a missing date 😱",
            "date": None,
            "committer_date": None,
            "type": "git",
            "directory": "c6dcbe9711ea6d5a31429a833a3d0c59cbbb2578",
            "synthetic": False,
            "metadata": {},
            "parents": [],
            "id": "1111111111111111111111111111111111111111",
            "extra_headers": [],
            "url": "https://archive.softwareheritage.org/api/1/revision/1111111111111111111111111111111111111111/",
            "history_url": "https://archive.softwareheritage.org/api/1/revision/1111111111111111111111111111111111111111/log/",
        }
    ),
}
