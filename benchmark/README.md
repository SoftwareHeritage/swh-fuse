# Quick'n'dirty fwh-FUSE benchmark

## Cases

 * Python SLOCs: glob `**/*.py`, open each file (in Python), count lines. Batches of 10 SWHIDs.
 * Python files: glob `**/*.py`, count files. Batches of 100 SWHIDs because FUSE should not be too slow, for once.

## Measures

Before each batch of SWHIDs, we `swh fs clean` so `swh-fuse`'s cache stays small.
For each SWHID we measure 4 runtimes:

* **cold FUSE** launch the case on `mountpoint/archive/swh:1:dir:...` - during this first run, `swh-fuse` has to make many API calls
* **hot FUSE** launch the same thing again: this time `swh-fuse` should have everything in its cache, so this measures FUSE's overhead
* **vault** downloads the directory from the archive, untar locally, runs the test.
* **baseline** is vault without the download/untar time, ie. measures how much time takes the case to run in a purely local setting.


## Method and potential biases

We pick SWHIDs randomly from the 12315 releases in
[2021-03-23-popular-3k-python/compressed/graph.nodes.csv](cf. https://docs.softwareheritage.org/devel/swh-graph/quickstart.html#retrieving-a-compressed-graph).
Randomness should ensure that the server side does not benefit from any cache...
but as there is only ~1200 origins, we can likely encounter some contents again during those tests.
The vault only works on directories,
so revision IDs are converted -
see `origins_to_directories.py` for the preparation step.
Restricting to Python releases may introduce biases, but we have to pick SWHIDs somewhere
and working on that dataset can allow us to later compare locally to a graph-based implem.

`bench.sh` helps to tidy up CSVs and related log files.
We use a custom logging configuration, to have `swh.fuse` in DEBUG with timestamps.
