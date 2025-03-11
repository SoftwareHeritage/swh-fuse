# 2025-03-11 First test of swh-fuse with a local graph+objstorage

## TLDR just give me numbers

We're reaching reasonable runtimes, even on cold start.
However waiting for the distant `storage` still accounts for 70% of the `swh-fuse` overhead.

When runnning ScanCode, `swh-fuse` takes only 10% more time on cold start, 0.7% more once filled.

When counting lines in `*.py` files, `swh-fuse` is 500 times slower on cold start, and 10 times slower with a pre-filled cache but maybe that's still unfair because the baseline has an NVMe.

## Setting

Running [swh-fuse@connecttoobjstorage](https://gitlab.softwareheritage.org/swh/devel/swh-fuse/-/merge_requests/95)
on `ddouard-desktop` because it has locally
 * an objstorage covering the `popular-python-500` graph (pathslicer over a hard drive).
 * a local compressed graph gRPC server (on popular-python-500)
 * connecting to `storage-ro.internal.staging.swh.network` (average RTT: 10ms)

In other words, FUSE is not contacting the WebAPI any more.

Two tests case, running over randomly picked releases among `popular-python-500`:
 - 100 runs of `scancode -clpieu` (ie. extensive analysis)
 - 100 runs of counting (in python) python lines of code

The first case is largely dominated by the computation itself,
whereas the second is pulling from `swh-fuse` as fast as it can.

Each run consists of
 * a vault download of said release - run is aborted if vault failed, because the case's runtime over the untarred folder is considered as baseline (however it's untarred to /tmp who's in an NVMe which is not fair, but I notice this as I'm writing the report. Harder conditions yield stronger modules, maybe)
 * running case over `mountpoint/archive/[releases' root]` , which we call "cold FUSE"
 * running the case again, this time we only hit our cache so it's "hot FUSE"

We put all swh-fuse caches in memory, and reset them after each pass so the cold run is really a cold start.

## Notes

 * `swh-vault` returns many 404 - ~40% failed on scancode case, 70% on python SLOC.
 * I remove 3 `scancode` runs because computation time went astray when running over the vault (although the vault replied as quickly as usual 🤔)

## Very soon

 * a third case using a middle-ground computation, [hyperpolyglot](https://github.com/monkslc/hyperpolyglot)
 * measuring memory consumption

## Soon

* using a local hashes map instead of calling `storage`
* playing with `swh-fuse` cache parameters, and removing its cache entirely because it's serializing so much to JSON.



# 2025-01-25 Quick'n'dirty fwh-FUSE benchmark

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
