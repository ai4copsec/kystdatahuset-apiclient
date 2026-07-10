# kystdatahuset-apiclient

A Python client for the [Kystdatahuset](https://kystdatahuset.no) REST API
([API docs](https://kystdatahuset.no/ws/swagger/index.html)). It handles
authentication and lets you look up ships and download NOR VTS incident
reports, saving them as JSON or a single Parquet file.

## Installation

Using [uv](https://docs.astral.sh/uv/) (recommended):

```shell
uv sync
```

Or with pip, into a virtual environment:

```shell
pip install .
```

This installs the `kystdata` command-line tool as well as the `kystdata`
Python package.

### Optional extras

- `test` — test dependencies (`pytest` and friends).
- `dev` — tooling used for development (linting, docs, `tox`).

```shell
uv sync --extra test
```

## Configuration

Credentials are your Kystdatahuset (kystinfo.no) login and are read from
environment variables or a `.env` file in the current working directory,
using the `KYSTDATA_APICLIENT_` prefix:

```shell
# .env
KYSTDATA_APICLIENT_USER=your-username
KYSTDATA_APICLIENT_PASSWORD=your-password
```

`KYSTDATA_APICLIENT_CSRF_TOKEN` is optional; a random one is generated if not
set.

## Command-line usage

```shell
kystdata --help
kystdata query --help
```

Authenticate and print the bearer token (useful for e.g. calling the API
directly with `curl`):

```shell
kystdata login
```

`query` supports several lookups, selected with `--lookup`
(`incidents` [default], `ship-mmsi`, `ship-callsign`, `ships-for-mmsis`):

```shell
kystdata query --lookup ship-mmsi --mmsi 257123456
kystdata query --lookup ship-callsign --callsign LA1234
kystdata query --lookup ships-for-mmsis --mmsi 257123456 477125300
```

For non-incident lookups, the result is written to a single file named
`kystdata-<lookup>.json` (or `.parquet`) in `--output-dir`; use
`--output-filename` to name it differently.

Download all NOR VTS incidents in a time window as individual JSON files:

```shell
kystdata query --from-time 2026-01-01 --to-time 2026-01-31
```

Download the same incidents into a single Parquet file:

```shell
kystdata query --from-time 2026-01-01 --to-time 2026-01-31 \
    --output-format parquet --output-dir ./out
```

This writes `./out/kystdata-incidents.parquet`. Use `--output-filename` to
name the file differently:

```shell
kystdata query --output-format parquet --output-dir ./out \
    --output-filename incidents-january.parquet
```

If `--from-time` / `--to-time` are omitted, all available incidents are
fetched. If `--output-dir` is omitted, files are written to a timestamped
directory under the system temp directory. For `--lookup incidents`,
`--output-filename` only applies to `--output-format parquet`; JSON output
always writes one file per incident named `<incident_id>.json`.

### Raw queries

For endpoints not (yet) wrapped by `query`, `raw` performs an authenticated
request against any endpoint path relative to the API base url
(`https://kystdatahuset.no/ws/api/`):

```shell
kystdata raw ship/combined/mmsi/257123456

kystdata raw kystinfo/norvts-incidents --method POST \
    --data '{"startTime": "2026-01-01T00:00:00", "endTime": "2026-01-31T23:59:59"}'
```

`--param key=value` adds query string parameters (repeatable), `--data` takes
a literal JSON string, `@<file>` to read the body from a file, or `-` to read
it from stdin. The (JSON) response is printed to stdout, or written to a file
with `--output`.

## Python API

```python
import datetime as dt

from kystdata.core.client import KystdataClient
from kystdata.core.config import Credentials, Incident

credentials = Credentials()
client = KystdataClient()
client.login(
    username=credentials.user,
    password=credentials.password,
    csrf_token=credentials.csrf_token,
)

incidents = client.lookup_norvts_incidents(
    from_time=dt.datetime(2026, 1, 1),
    to_time=dt.datetime(2026, 1, 31),
)
incident_models = [Incident(**incident) for incident in incidents]

df = Incident.get_dataframe(incident_models)
df.to_parquet("incidents.parquet")

client.logout()
```

Ship lookups:

```python
client.lookup_ship_mmsi("257123456")
client.lookup_ship_callsign("LA1234")
client.lookup_ships_for_mmsis(["257123456", "477125300"])
```

## Development

Common tasks are wrapped in a [`Justfile`](Justfile) — install
[`just`](https://github.com/casey/just) and run:

```shell
just sync   # uv sync --all-extras
just test   # run the test suite
just lint   # run pre-commit hooks (ruff, isort, ...)
just docs   # build the quartodoc API reference and render the docs site
```

Without `just`, the equivalent commands are:

```shell
uv sync --extra test
uv run pytest
```

## Documentation

The docs site (under [`docs/`](docs)) is built with
[Quarto](https://quarto.org) and [quartodoc](https://machow.github.io/quartodoc)
for the Python API reference:

```shell
just docs           # build once
just docs-preview   # live-reload preview
```
