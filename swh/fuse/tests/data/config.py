# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

""" Use the Rust compiler (v1.42.0) as a testing repository """

# Content
REGULAR_FILE = "swh:1:cnt:61d3c9e1157203f0c4ed5165608d92294eaca808"
# Directory
ROOT_DIR = "swh:1:dir:c6dcbe9711ea6d5a31429a833a3d0c59cbbb2578"
DIR_WITH_SUBMODULES = "swh:1:dir:80ae84abc6122c47aae597fde99645f8663d1aba"
# Revision
ROOT_REV = "swh:1:rev:b8cedc00407a4c56a3bda1ed605c6fc166655447"
SUBMODULES = [
    "swh:1:rev:87dd6843678575f8dda962f239d14ef4be14b352",
    "swh:1:rev:1a2390247ad6d08160e0dd74f40a01a9578659c2",
    "swh:1:rev:4d78994915af1bde9a95c04a8c27d8dca066232a",
    "swh:1:rev:3e6e1001dc6e095dbd5c88005e80969f60e384e1",
    "swh:1:rev:11e893fc1357bc688418ddf1087c2b7aa25d154d",
    "swh:1:rev:1c2bd024d13f8011307e13386cf1fea2180352b5",
    "swh:1:rev:92baf7293dd2d418d2ac4b141b0faa822075d9f7",
]
# Release
# TODO
# Snapshot
# TODO

ALL_ENTRIES = [REGULAR_FILE, ROOT_DIR, DIR_WITH_SUBMODULES, ROOT_REV, *SUBMODULES]
