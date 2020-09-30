# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

# WARNING: do not import unnecessary things here to keep cli startup time under
# control
from pathlib import Path
from typing import Any, Dict

import click

# from swh.core import config
from swh.core.cli import CONTEXT_SETTINGS
from swh.model.identifiers import SWHID

# All generic config code should reside in swh.core.config
DEFAULT_CONFIG_PATH = os.environ.get(
    "SWH_CONFIG_FILE", os.path.join(click.get_app_dir("swh"), "global.yml")
)

CACHE_HOME_DIR: Path = (
    Path(os.environ["XDG_CACHE_HOME"])
    if "XDG_CACHE_HOME" in os.environ
    else Path(Path.home(), ".cache")
)

DEFAULT_CONFIG: Dict[str, Any] = {
    "cache-dir": Path(CACHE_HOME_DIR, "swh", "fuse"),
    "web-api": {
        "url": "https://archive.softwareheritage.org/api/1",
        "auth-token": None,
    },
}


class SWHIDParamType(click.ParamType):
    """Click argument that accepts SWHID and return them as
    :class:`swh.model.identifiers.SWHID` instances

    """

    name = "SWHID"

    def convert(self, value, param, ctx) -> SWHID:
        from swh.model.exceptions import ValidationError
        from swh.model.identifiers import parse_swhid

        try:
            return parse_swhid(value)
        except ValidationError:
            self.fail(f'"{value}" is not a valid SWHID', param, ctx)


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
    "-c",
    "--cache-dir",
    default=DEFAULT_CONFIG["cache-dir"],
    metavar="CACHE_DIR",
    show_default=True,
    type=click.Path(dir_okay=True, file_okay=False),
    help="""
        directory where to store cache from the Software Heritage API. To
        store all the cache in memory instead of disk, use a value of ':memory:'.
    """,
)
@click.option(
    "-u",
    "--api-url",
    default=DEFAULT_CONFIG["web-api"]["url"],
    metavar="API_URL",
    show_default=True,
    help="base URL for Software Heritage Web API",
)
@click.option(
    "-f",
    "--foreground",
    is_flag=True,
    show_default=True,
    help="Run FUSE system in foreground instead of daemon",
)
@click.pass_context
def mount(ctx, swhids, path, cache_dir, api_url, foreground):
    """ Mount the Software Heritage archive at the given mount point """

    from swh.fuse import fuse

    if foreground:
        fuse.main(swhids, path, cache_dir, api_url)
    else:
        import daemon

        with daemon.DaemonContext():
            fuse.main(swhids, path, cache_dir, api_url)
