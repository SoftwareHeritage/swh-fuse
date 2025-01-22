# Quick'n'dirty fwh-FUSE benchmark

## Test cases

 * Counting Python SLOCs: glob `**/*.py`, open each file (in Python), count lines.
 * Counting Python files: glob `**/*.py`, count resulting files. This one does not access files' content, so it should be the fastest.
 * Scancode: `scancode -clpieu --json-pp [swhid.json] [swhid]` ie. a pretty complete report.


## Measures

For each SWHID we measure 4 runtimes:

* **vault** downloads the directory from the archive, untar locally, runs the test.
* **baseline** is vault without the download/untar time, ie. measures how much time takes the case to run in a purely local setting.
* **cold FUSE** launch the case on `mountpoint/archive/swh:1:dir:...` - during this first run, `swh-fuse` has to make *many* calls to the SWH Web API (one per traversed inode).
* **hot FUSE** launch the same case again: this time `swh-fuse` should have everything in its cache, so this measures FUSE's overhead


## Results summary

"Cold FUSE" is so slow (up to 7h on a single release folder) that it limits the number of cases we could run: 4 for ScanCode, 2 SLOC counts, 16 files counting... and its cache is not remembering everything by default.
"Hot FUSE" is much faster, and its logs confirm it almost does not make any API query. In other words, the bottleneck of cold FUSE is API calls, as expected.

For a complex task like ScanCode, vault does not add much overhead, below 4%.
Hot FUSE is on par with local FS, and does not uses much CPU while ScanCode runs (less than 3s of CPU time while ScanCode took 80s).

Complete results are in `results.ods` in this folder.

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
