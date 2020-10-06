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
from typing import Any, Dict, Tuple

import click
from daemon import DaemonContext

# from swh.core import config
from swh.core.cli import CONTEXT_SETTINGS
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

DEFAULT_CONFIG: Dict[str, Tuple[str, Any]] = {
    "cache": (
        "dict",
        {
            "metadata": {"path": CACHE_HOME_DIR / "swh/fuse/metadata.sqlite"},
            "blob": {"path": CACHE_HOME_DIR / "swh/fuse/blob.sqlite"},
        },
    ),
    "web-api": (
        "dict",
        {"url": "https://archive.softwareheritage.org/api/1", "auth-token": None,},
    ),
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
@click.argument(
    "path",
    required=True,
    metavar="PATH",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
)
@click.argument("swhids", nargs=-1, metavar="[SWHID]...", type=SWHIDParamType())
@click.option(
    "--config-file",
    "-C",
    default=None,
    type=click.Path(exists=True, dir_okay=False,),
    help="YAML configuration file",
)
@click.option(
    "-f",
    "--foreground",
    is_flag=True,
    show_default=True,
    help="Run FUSE system in foreground instead of daemon",
)
@click.pass_context
def mount(ctx, swhids, path, config_file, foreground):
    """ Mount the Software Heritage archive at the given mount point """

    from swh.core import config
    from swh.fuse import fuse

    conf = config.read(config_file, DEFAULT_CONFIG)
    with ExitStack() as stack:
        if not foreground:
            stack.enter_context(DaemonContext())
        asyncio.run(fuse.main(swhids, path, conf))
