# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

""" Use the Rust compiler (v1.42.0) as a testing repository """


def remove_swhid_prefix(swhid_str: str) -> str:
    prefix = "swh:1:XXX:"
    return swhid_str[len(prefix) :]


# Content
REGULAR_FILE = "swh:1:cnt:61d3c9e1157203f0c4ed5165608d92294eaca808"
# Directory
ROOT_DIR = "swh:1:dir:c6dcbe9711ea6d5a31429a833a3d0c59cbbb2578"
# Directory (symlinks entries)
CNT_SYMLINK = "swh:1:cnt:76219eb72e8524f15c21ec93b9b2592da49b5460"  # from rust-clippy
DIR_WITH_CNT_SYMLINK = "swh:1:dir:8f04a97403e13995c8790aef9158c8981b026223"
DIR_SYMLINK = "swh:1:cnt:e8310385c56dc4bbe379f43400f3181f6a59f260"  # from Limnoria
DIR_WITH_DIR_SYMLINK = "swh:1:dir:0653a2af52ebb771ef8ce0388c942d77f9d7aee8"
REV_SYMLINKS = [  # from rust compiler
    "swh:1:rev:87dd6843678575f8dda962f239d14ef4be14b352",
    "swh:1:rev:1a2390247ad6d08160e0dd74f40a01a9578659c2",
    "swh:1:rev:4d78994915af1bde9a95c04a8c27d8dca066232a",
    "swh:1:rev:3e6e1001dc6e095dbd5c88005e80969f60e384e1",
    "swh:1:rev:11e893fc1357bc688418ddf1087c2b7aa25d154d",
    "swh:1:rev:1c2bd024d13f8011307e13386cf1fea2180352b5",
    "swh:1:rev:92baf7293dd2d418d2ac4b141b0faa822075d9f7",
]
DIR_WITH_REV_SYMLINK = "swh:1:dir:80ae84abc6122c47aae597fde99645f8663d1aba"
# Revision
ROOT_REV = "swh:1:rev:b8cedc00407a4c56a3bda1ed605c6fc166655447"
REV_SMALL_HISTORY = "swh:1:rev:37426e42cf78a43779312d780eecb21a64006d99"
# Release
ROOT_REL = "swh:1:rel:874f7cbe352033cac5a8bc889847da2fe1d13e9f"
# Snapshot
# WARNING: Do not use a snapshot artifact which is paginated because it will be
# a pain to synchronize formats properly between the mock Web API/Web API Client
# (since they differ slightly for snapshots). The Web API Client is already
# responsible for merging everything together so the real API will have no
# problem, only the mock offline one.
ROOT_SNP = "swh:1:snp:02db117fef22434f1658b833a756775ca6effed0"
ROOT_SNP_MASTER_BRANCH = "swh:1:rev:430a9fd4c797c50cea26157141b2408073b2ed91"
FAKE_SNP_SPECIAL_CASES_SWHID = "swh:1:snp:0000000000000000000000000000000000000000"
FAKE_SNP_SPECIAL_CASES = {
    # All possible target types
    "mycnt": {"target_type": "content", "target": remove_swhid_prefix(REGULAR_FILE),},
    "mydir": {"target_type": "directory", "target": remove_swhid_prefix(ROOT_DIR),},
    "myrev": {"target_type": "revision", "target": remove_swhid_prefix(ROOT_REV),},
    "myrel": {"target_type": "release", "target": remove_swhid_prefix(ROOT_REL),},
    "refs/heads/master": {
        "target_type": "revision",
        "target": remove_swhid_prefix(ROOT_SNP_MASTER_BRANCH),
    },
    # Alias with different target paths
    "alias-rootdir": {
        "target_type": "alias",
        "target": "refs/heads/master",
        "expected_symlink": "refs/heads/master",
    },
    "refs/heads/alias-subdir": {
        "target_type": "alias",
        "target": "refs/heads/master",
        "expected_symlink": "master",
    },
    "refs/tags/alias-different-subdir": {
        "target_type": "alias",
        "target": "refs/heads/master",
        "expected_symlink": "../heads/master",
    },
}
# Origin
ORIGIN_URL = "https://github.com/rust-lang/rust"
ORIGIN_URL_ENCODED = "https%3A%2F%2Fgithub.com%2Frust-lang%2Frust"

# Special corner cases (not from Rust compiler)
REL_TARGET_CNT = "swh:1:rel:da5f9898d6248ab26277116f54aca855338401d2"
TARGET_CNT = "swh:1:cnt:be5effea679c057aec2bb020f0241b1d1d660840"
REL_TARGET_DIR = "swh:1:rel:3a7b2dfffed2945d2933ba4ebc063adba35ddb2e"
TARGET_DIR = "swh:1:dir:b24d39c928b9c3f440f8e2ec06c78f43d28d87d6"

ALL_ENTRIES = [
    REGULAR_FILE,
    ROOT_DIR,
    CNT_SYMLINK,
    DIR_SYMLINK,
    *REV_SYMLINKS,
    DIR_WITH_CNT_SYMLINK,
    DIR_WITH_DIR_SYMLINK,
    DIR_WITH_REV_SYMLINK,
    ROOT_REV,
    REV_SMALL_HISTORY,
    ROOT_REL,
    REL_TARGET_CNT,
    REL_TARGET_DIR,
    ROOT_SNP,
    ROOT_SNP_MASTER_BRANCH,
]
