# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

# WARNING: do not import unnecessary things here to keep cli startup time under
# control
import os
from typing import Any, Dict

import click

# from swh.core import config
from swh.core.cli import CONTEXT_SETTINGS

# All generic config code should reside in swh.core.config
DEFAULT_CONFIG_PATH = os.environ.get(
    "SWH_CONFIG_FILE", os.path.join(click.get_app_dir("swh"), "global.yml")
)

DEFAULT_CONFIG: Dict[str, Any] = {
    "web-api": {
        "url": "https://archive.softwareheritage.org/api/1",
        "auth-token": None,
    }
}


@click.group(name="fuse", context_settings=CONTEXT_SETTINGS)
# XXX  conffile logic temporarily commented out due to:
# XXX  https://forge.softwareheritage.org/T2632
# @click.option(
#     "-C",
#     "--config-file",
#     default=DEFAULT_CONFIG_PATH,
#     type=click.Path(exists=True, dir_okay=False, path_type=str),
#     help="YAML configuration file",
# )
@click.pass_context
def cli(ctx):
    """Software Heritage virtual file system"""

    # # recursive merge not done by config.read
    # conf = config.read_raw_config(config.config_basepath(config_file))
    # conf = config.merge_configs(DEFAULT_CONFIG, conf)
    conf = {}

    ctx.ensure_object(dict)
    ctx.obj["config"] = conf


@cli.command()
@click.option(
    "-u",
    "--api-url",
    default=DEFAULT_CONFIG["web-api"]["url"],
    metavar="API_URL",
    show_default=True,
    help="base URL for Software Heritage Web API",
)
@click.pass_context
def mount(ctx, api_url):
    """Mount the Software Heritage archive at the given mount point"""
    from .fuse import fuse  # XXX

    fuse()
