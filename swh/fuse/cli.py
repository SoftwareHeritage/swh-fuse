# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
from contextlib import ExitStack
import os

# WARNING: do not import unnecessary things here to keep cli startup time under
# control
from pathlib import Path
from typing import Any, Dict

import click
from daemon import DaemonContext

from swh.core import config
from swh.core.cli import CONTEXT_SETTINGS
from swh.core.cli import swh as swh_cli_group
from swh.model.cli import SWHIDParamType

# All generic config code should reside in swh.core.config
DEFAULT_CONFIG_PATH = os.environ.get(
    "SWH_CONFIG_FILE", os.path.join(click.get_app_dir("swh"), "global.yml")
)

CACHE_HOME_DIR: Path = (
    Path(os.environ["XDG_CACHE_HOME"])
    if "XDG_CACHE_HOME" in os.environ
    else Path.home() / ".cache"
)

DEFAULT_CONFIG: Dict[str, Any] = {
    "cache": {
        "metadata": {"path": CACHE_HOME_DIR / "swh/fuse/metadata.sqlite"},
        "blob": {"path": CACHE_HOME_DIR / "swh/fuse/blob.sqlite"},
    },
    "web-api": {
        "url": "https://archive.softwareheritage.org/api/1",
        "auth-token": None,
    },
}


@swh_cli_group.group(name="fuse", context_settings=CONTEXT_SETTINGS)
@click.option(
    "-C",
    "--config-file",
    default=None,
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help=f"Configuration file (default: {DEFAULT_CONFIG_PATH})",
)
@click.pass_context
def fuse(ctx, config_file):
    """Software Heritage virtual file system"""

    if not config_file and config.config_exists(DEFAULT_CONFIG_PATH):
        config_file = DEFAULT_CONFIG_PATH

    if not config_file:
        conf = DEFAULT_CONFIG
    else:
        # recursive merge not done by config.read
        conf = config.read_raw_config(config.config_basepath(config_file))
        conf = config.merge_configs(DEFAULT_CONFIG, conf)

    ctx.ensure_object(dict)
    ctx.obj["config"] = conf


@fuse.command(name="mount")
@click.argument(
    "path",
    required=True,
    metavar="PATH",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
)
@click.argument("swhids", nargs=-1, metavar="[SWHID]...", type=SWHIDParamType())
@click.option(
    "-f/-d",
    "--foreground/--daemon",
    default=False,
    help="whether to run FUSE attached to the console (foreground) "
    "or daemonized in the background (default: daemon)",
)
@click.pass_context
def mount(ctx, swhids, path, foreground):
    """Mount the Software Heritage archive at PATH

    If specified, objects referenced by the given SWHIDs will be prefetched and used to
    populate the virtual file system (VFS). Otherwise the VFS will be populated
    on-demand, when accessing its content.

    \b
    Example:

    \b
      $ mkdir swhfs
      $ swh fuse mount swhfs/
      $ grep printf swhfs/archive/swh:1:cnt:c839dea9e8e6f0528b468214348fee8669b305b2
          printf("Hello, World!");
      $

    """

    from swh.fuse import fuse

    with ExitStack() as stack:
        if not foreground:
            # Stay in the current working directory when spawning daemon
            cwd = os.getcwd()
            stack.enter_context(DaemonContext(working_directory=cwd))
        asyncio.run(fuse.main(swhids, path, ctx.obj["config"]))
