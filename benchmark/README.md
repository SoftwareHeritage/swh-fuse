# 2025-04-14 First 100% local swh-fuse on python-popular-500k

## Setting

Very similar to the 2025-03-11 bench (see below), but we added
 * a [digestmap](https://gitlab.softwareheritage.org/swh/devel/swh-digestmap/-/merge_requests/3), read via the Python binding, able to map locally SWHIDs to SHA1 for contents in this graph
 * a third test case with [hyperpolyglot](https://github.com/monkslc/hyperpolyglot) a language detector implemented in Rust (it's fast!),
   hopyfully slower than counting Python LOC in Python but faster than Scancode

## Results are OK

Detailed results are in `.ods` in benchmark folders:
[folder1](https://gitlab.softwareheritage.org/swh/devel/swh-fuse/-/tree/bench/benchmark/2025-04-10?ref_type=heads)
[folder2](https://gitlab.softwareheritage.org/swh/devel/swh-fuse/-/tree/bench/benchmark/2025-04-14_nocache?ref_type=heads)

* in that setting most of the "cold fuse" overhead is spent waiting for the `graph-grpc` server (even locally), which is expected as it's the most complex service in the stack
* Scancode is so slow (even running only `--licence`) that there's no significant difference between FUSE/vault
* a first access via FUSE takes ~50 more times than the computation itself
  + variance is non-negligible: on that grade minimum is 6 times longer, maximum 200 times longer... but all this is sub-second
* Hyperpolyglot is a bit faster than our Python lines counter 😅 and it's multi-threaded so we're not reporting FUSE's waiting times correctly in that case
* Even on cold start, running cases via fuse is vaguely 5 times faster than downloading from the vault (but it's much much farther away)

## Should we cut swh.fuse.cache ?

Also ran a bonus variant, [removing `swh.fuse.cache`](https://gitlab.softwareheritage.org/martin/swh-fuse/-/commit/ebcac8b2b3f869bda48a8908e957a5a4de321dac)
Granted, that module provides a fancy configurable cache - but it's deeply intricated in
the implementation, and forces all meta-data through a JSON (de)serialization. What
happens if we remove it entirely ?

Note that this comparison was not made as consecutive runs on the same content with/without cache, but as a second batch running against the vault again.
So numbers below still use the uncompressed vault archive as a baseline.

* Hyperpolyglot (who's multi-threaded) was 56 times slower on cold-FUSE / 13 times when cached
  + without the caching module, it's 17 times slower, 4 times when cached
* PythonLOC counter was 53 times slower, 10 times when cached
  + without the caching module, it's 50 times/ 10 times when cached
* Scancode is too slow

so it is a bit faster, but
 * `swh.fuse.cache` still provides a configurable, potentially persistant, cache, which is
still relevant for WebAPI users - that is, people developping FUSE traversers.
* in the final setting nothing will be local, so FUSE will spend most of its wall-clock time waiting for distant services anyway

so let's keep that cache, it's time to run a full-scale test.



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
