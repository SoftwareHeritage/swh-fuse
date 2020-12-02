# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

# WARNING: do not import unnecessary things here to keep cli startup time under
# control
import os
from pathlib import Path
from typing import Any, Dict

import click

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
        "metadata": {"path": str(CACHE_HOME_DIR / "swh/fuse/metadata.sqlite")},
        "blob": {"path": str(CACHE_HOME_DIR / "swh/fuse/blob.sqlite")},
        "direntry": {"maxram": "10%"},
    },
    "web-api": {
        "url": "https://archive.softwareheritage.org/api/1",
        "auth-token": None,
    },
    "json-indent": 2,
}


@swh_cli_group.group(name="fs", context_settings=CONTEXT_SETTINGS)
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

    import logging

    import yaml

    from swh.core import config

    if not config_file:
        config_file = DEFAULT_CONFIG_PATH

    try:
        conf = config.read_raw_config(config.config_basepath(config_file))
        if not conf:
            raise ValueError(f"Cannot parse configuration file: {config_file}")

        if config_file == DEFAULT_CONFIG_PATH:
            try:
                conf = conf["swh"]["fuse"]
            except KeyError:
                pass

        # recursive merge not done by config.read
        conf = config.merge_configs(DEFAULT_CONFIG, conf)
    except Exception:
        logging.warning(
            "Using default configuration (cannot load custom one)", exc_info=True
        )
        conf = DEFAULT_CONFIG

    logging.debug("Read configuration: \n%s", yaml.dump(conf))
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
    """Mount the Software Heritage virtual file system at PATH.

    If specified, objects referenced by the given SWHIDs will be prefetched and used to
    populate the virtual file system (VFS). Otherwise the VFS will be populated
    on-demand, when accessing its content.

    \b
    Example:

    \b
      $ mkdir swhfs
      $ swh fs mount swhfs/
      $ grep printf swhfs/archive/swh:1:cnt:c839dea9e8e6f0528b468214348fee8669b305b2
          printf("Hello, World!");
      $

    """

    import asyncio
    from contextlib import ExitStack
    import logging

    from daemon import DaemonContext

    from swh.fuse import LOGGER_NAME, fuse

    # TODO: set default logging settings when --log-config is not passed
    # DEFAULT_LOG_PATH = Path(".local/swh/fuse/mount.log")
    with ExitStack() as stack:
        if not foreground:
            # TODO: temporary fix until swh.core has the proper logging utilities
            # Disable logging config before daemonizing, and reset it once
            # daemonized to be sure to not close file handlers
            log_level = logging.getLogger(LOGGER_NAME).getEffectiveLevel()
            logging.shutdown()
            # Stay in the current working directory when spawning daemon
            cwd = os.getcwd()
            stack.enter_context(DaemonContext(working_directory=cwd))
            logging.config.dictConfig(
                {
                    "version": 1,
                    "handlers": {
                        "syslog": {
                            "class": "logging.handlers.SysLogHandler",
                            "address": "/dev/log",
                        },
                    },
                    "loggers": {
                        LOGGER_NAME: {"level": log_level, "handlers": ["syslog"],},
                    },
                }
            )

        conf = ctx.obj["config"]
        asyncio.run(fuse.main(swhids, path, conf))


@fuse.command()
@click.argument(
    "path",
    required=True,
    metavar="PATH",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
)
@click.pass_context
def umount(ctx, path):
    """Unmount a mounted virtual file system.

    Note: this is equivalent to ``fusermount -u PATH``, which can be used to unmount any
    FUSE-based virtual file system. See ``man fusermount3``.

    """
    import logging
    import subprocess

    try:
        subprocess.run(["fusermount", "-u", path], check=True)
    except subprocess.CalledProcessError as err:
        logging.error(
            "cannot unmount virtual file system: '%s' returned exit status %d",
            " ".join(err.cmd),
            err.returncode,
        )
        ctx.exit(1)


@fuse.command()
@click.pass_context
def clean(ctx):
    """Clean on-disk cache(s).

    """

    def rm_cache(conf, cache_name):
        try:
            Path(conf["cache"][cache_name]["path"]).unlink()
        except (FileNotFoundError, KeyError):
            pass

    conf = ctx.obj["config"]
    for cache_name in ["blob", "metadata"]:
        rm_cache(conf, cache_name)
