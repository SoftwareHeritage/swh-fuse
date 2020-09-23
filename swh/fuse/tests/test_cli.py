# Copyright (C) 2020 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from click.testing import CliRunner

from swh.fuse import cli


class TestMount(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_no_args(self):
        result = self.runner.invoke(cli.mount)
        self.assertNotEqual(result.exit_code, 0)
