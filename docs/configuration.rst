.. _swh-fuse-config:

Configuration
=============

All configuration for the Software Heritage virtual file system should be done
in a single `.yml` file, containing the following fields:

- `cache`:

  - `metadata`: where to store the metadata cache, must have either a
    `in-memory` boolean entry or a `path` string entry (with the corresponding
    disk path)
  - `blob`: where to store the blob cache, same entries as the `metadata` cache

- `web-api`:

  - `url`: archive API URL
  - `auth-token`: authentication token used with the API URL

Set the `-C/--config-file` option of the :ref:`CLI <swh-fuse-cli>` to use your
configuration file.

If no configuration is given, default values are:

- `cache`: all cache files are stored in `$XDG_CACHE_HOME/swh/fuse/` (or
  `$HOME/.cache/swh/fuse` if `XDG_CACHE_HOME` is not set)
- `web-api`: default URL is https://archive.softwareheritage.org/api/1/ (with no
  authentication token)


Example
-------

Here is a complete example showcasing different cache storage strategies
(in-memory for metadata and on-disk for blob), using the default Web API
service:

.. code:: yaml

    cache:
      metadata:
        in-memory: true
      blob:
        path: "/path/to/cache/blob.sqlite"
    web-api:
      url: "https://archive.softwareheritage.org/api/1/"
      auth-token: null
