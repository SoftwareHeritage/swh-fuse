# Copyright (C) 2020 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from click.testing import CliRunner
import yaml

import swh.fuse.cli as cli

# mount/umount commands are already tested when setting up the fuse_mntdir fixture


def test_clean_command(tmp_path):
    fake_metadata_db = tmp_path / "metadata.sqlite"
    fake_blob_db = tmp_path / "blob.sqlite"
    config_path = tmp_path / "config.yml"
    config = {
        "cache": {
            "metadata": {"path": str(fake_metadata_db)},
            "blob": {"path": str(fake_blob_db)},
        },
    }

    fake_metadata_db.touch()
    fake_blob_db.touch()
    config_path.write_text(yaml.dump(config))

    assert fake_metadata_db.exists()
    assert fake_blob_db.exists()

    CliRunner().invoke(
        cli.fuse, args=["--config-file", str(config_path), "clean",],
    )

    assert not fake_metadata_db.exists()
    assert not fake_blob_db.exists()
