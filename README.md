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

- `dp` — installs [`damast`](https://github.com/damast) to support building
  an `AnnotatedDataFrame` from incidents (`Incident.get_annotated_dataframe`).
- `test` — test dependencies (`pytest` and friends).
- `dev` — tooling used for development (linting, docs, `tox`).

```shell
uv sync --extra dp --extra test
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
directory under the system temp directory. `--output-filename` only applies
to `--output-format parquet`; JSON output always writes one file per incident
named `<incident_id>.json`.

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
```

## Development

```shell
uv sync --extra test
uv run pytest
```
