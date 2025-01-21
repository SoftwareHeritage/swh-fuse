#!/usr/bin/env python
from pathlib import Path
import os
from sys import stderr

import click
import yaml

from swh.web.client.client import WebAPIClient

conf_path = os.path.join(click.get_app_dir("swh"), "global.yml")
conf = yaml.load(open(conf_path), Loader=yaml.FullLoader)
token = conf['swh']['fuse']['web-api']['auth-token']

client = WebAPIClient(bearer_token=token)

def rel_info(swhid):
    release = client.get(swhid)
    rev = client.get(release['target'])
    try:
        print(rev['directory'])
    except KeyError:
        print(f"no directory for {swhid}", file=stderr)

@click.command()
@click.argument('csvpath', type=click.Path(exists=True, dir_okay=False))
def main(csvpath:Path):
    """
    turns a listing of revision SWHIDs into a list of their target directories.
    non-revision SWHIDs are ignored.

    expects a swh.fuse.web-api.auth-token in ~/.config/swh/global.yml

    Use for example 2021-03-23-popular-3k-python/compressed/graph.nodes.csv

    cf. https://docs.softwareheritage.org/devel/swh-graph/quickstart.html#retrieving-a-compressed-graph
    """
    with open(csvpath) as fp:
        for line in fp:
            if line.startswith("swh:1:rel:"):
                rel_info(line.strip())

if __name__ == '__main__':
    main()