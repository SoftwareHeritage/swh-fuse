#!/usr/bin/env python
from pathlib import Path
import os
from sys import stderr
from typing import Optional

import grpc
import click
import yaml

from swh.model.swhids import CoreSWHID, ObjectType
import swh.graph.grpc.swhgraph_pb2 as swhgraph
import swh.graph.grpc.swhgraph_pb2_grpc as swhgraph_grpc


conf_path = os.path.join(click.get_app_dir("swh"), "global.yml")
conf = yaml.load(open(conf_path), Loader=yaml.FullLoader)
token = conf["swh"]["fuse"]["web-api"]["auth-token"]

grpc_stub = swhgraph_grpc.TraversalServiceStub(
    grpc.insecure_channel(conf["swh"]["fuse"]["graph"]["grpc-url"])
)


def rel_info(swhid:str):
    try:
        node = grpc_stub.GetNode(swhgraph.GetNodeRequest(swhid=swhid))
    except grpc.RpcError as err:
        # probably does not exist in that graph
        return
    for successor in node.successor:
        target = CoreSWHID.from_string(successor.swhid)
        break
    else:
        return

    root = None
    if target.object_type == ObjectType.RELEASE:
        rel_info(str(target))
    elif target.object_type == ObjectType.REVISION:
        rev_node = grpc_stub.GetNode(swhgraph.GetNodeRequest(swhid=str(target)))
        for successor in rev_node.successor:
            successor_swhid = CoreSWHID.from_string(successor.swhid)
            if successor_swhid.object_type == ObjectType.DIRECTORY:
                root = successor_swhid
                break
        else:
            return
    elif target.object_type == ObjectType.DIRECTORY:
        root = target

    if root:
        print(str(root))


@click.command()
@click.argument("csvpath", type=click.Path(exists=True, dir_okay=False))
def main(csvpath: Path):
    """
    turns a listing of revision SWHIDs into a list of their target directories,
    using a graph via gRPC.

    Use for example 2021-03-23-popular-3k-python/compressed/graph.nodes.csv

    """
    with open(csvpath) as fp:
        for line in fp:
            if line.startswith("swh:1:rel:"):
                rel_info(line.strip())


if __name__ == "__main__":
    main()
