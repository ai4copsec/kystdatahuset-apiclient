import datetime as dt
import json
import logging
import tempfile
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from kystdata.cli.base import BaseParser
from kystdata.core.client import KystdataClient
from kystdata.core.config import (
    DATE_FORMAT,
    Credentials,
    Incident,
)

logger = logging.getLogger(__name__)

LOOKUP_CHOICES = ["incidents", "ship-mmsi", "ship-callsign", "ships-for-mmsis"]

class QueryParser(BaseParser):
    """
    :param parser: The base parser
    """

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser=parser)

        parser.description = "kystdata query"

        parser.add_argument("--lookup", type=str, default="incidents", choices=LOOKUP_CHOICES,
                            help="Which lookup to perform, default: %(default)s")

        parser.add_argument("--from-time", type=str, help="Starting date in the format YYYY-mm-dd (--lookup incidents)")
        parser.add_argument("--to-time", type=str, help="End date in the format YYYY-mm-dd (--lookup incidents)")

        parser.add_argument("--mmsi", type=str, nargs="+", default=None,
                            help="MMSI number(s) (--lookup ship-mmsi / ships-for-mmsis)")
        parser.add_argument("--callsign", type=str, default=None,
                            help="Callsign (--lookup ship-callsign)")

        #parser.add_argument("--from-lat", type=float, help="Lower bound for latitude")
        #parser.add_argument("--to-lat", type=float, help="Upper bound for latitude")

        #parser.add_argument("--from-lon", type=float, help="Lower bound for longitude")
        #parser.add_argument("--to-lon", type=float, help="Upper bound for longitude")

        #parser.add_argument("--at-lat", type=float, default=None, help="At latitude")
        #parser.add_argument("--at-lon", type=float, default=None, help="At longitude")
        #parser.add_argument("--radius", type=float, default=None, help="Radius in km")

        #parser.add_argument("--region", type=Path, default=None, help="A geojson file describing a region")

        #parser.add_argument("--report-type", nargs="+", default=None, type=ReportType, choices=list(ReportType), help="Report type default: %(default)s")
        #parser.add_argument("--impact", nargs="+", type=Impact, default=None, choices=list(Impact), help="Impact default: %(default)s")
        #parser.add_argument("--country", nargs="+", type=str, default=None, help="Countries: %(default)s")
        #parser.add_argument("--category", nargs="+", type=str, default=None, help="Categories: %(default)s")

        #parser.add_argument("--report-id", type=int, default=None)

        default_output_dir = Path(tempfile.gettempdir()) / "kystdata-query" / f"{dt.datetime.now(tz=dt.timezone.utc).strftime('%Y%m%d-%H:%M:%S+00:00')}"
        parser.add_argument("--output-dir", type=str, default=str(default_output_dir), help="Output directory to store the report jsons, default: %(default)s")
        parser.add_argument("--output-format", type=str,  default='json', choices=['json', 'parquet'], help="Output plain json files, or converted into a single parquet file")
        parser.add_argument("--output-filename", type=str, default=None,
                            help="Filename for the combined output file (only used with --output-format parquet, "
                                 "and always for non-incident lookups), default: kystdata-<lookup>.<format>")

    def _lookup_incidents(self, client: KystdataClient, args) -> list[Incident]:
        from_time = dt.datetime.strptime(args.from_time, DATE_FORMAT) if args.from_time else None
        to_time = dt.datetime.strptime(args.to_time, DATE_FORMAT) if args.to_time else None
        if to_time is not None:
            to_time = to_time.replace(hour=23, minute=59, second=59, microsecond=999999)

        incidents = client.lookup_norvts_incidents(from_time=from_time, to_time=to_time) or []
        return [incident if isinstance(incident, Incident) else Incident(**incident) for incident in incidents]

    def _lookup_records(self, client: KystdataClient, args) -> list:
        if args.lookup == 'incidents':
            return self._lookup_incidents(client, args)

        if args.lookup == 'ship-mmsi':
            if not args.mmsi:
                raise ValueError("--mmsi is required for --lookup ship-mmsi")
            if len(args.mmsi) > 1:
                logger.warning("--lookup ship-mmsi only resolves a single MMSI, using the first one: %s", args.mmsi[0])
            return [client.lookup_ship_mmsi(args.mmsi[0])]

        if args.lookup == 'ship-callsign':
            if not args.callsign:
                raise ValueError("--callsign is required for --lookup ship-callsign")
            return [client.lookup_ship_callsign(args.callsign)]

        if args.lookup == 'ships-for-mmsis':
            if not args.mmsi:
                raise ValueError("--mmsi is required for --lookup ships-for-mmsis")
            return client.lookup_ships_for_mmsis(args.mmsi) or []

        raise ValueError(f"Unsupported lookup: {args.lookup}")

    def _save_incidents(self, incidents: list[Incident], args, output_dir: Path) -> None:
        if args.output_format == 'json':
            logger.info(f"Saving incidents (.json) in {output_dir}")
            for incident in tqdm(incidents, desc="Incident:"):
                incident_path = output_dir / f"{incident.incident_id}.json"
                incident_path.write_text(incident.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
        else:
            output_path = output_dir / (args.output_filename or "kystdata-incidents.parquet")
            logger.info(f"Saving all incidents (.parquet) to {output_path}")
            adf = Incident.get_annotated_dataframe(incidents)
            adf.export(output_path)

    def _save_records(self, records: list, args, output_dir: Path) -> None:
        if args.output_format == 'json':
            output_path = output_dir / (args.output_filename or f"kystdata-{args.lookup}.json")
            logger.info(f"Saving {args.lookup} result (.json) to {output_path}")
            output_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            output_path = output_dir / (args.output_filename or f"kystdata-{args.lookup}.parquet")
            logger.info(f"Saving {args.lookup} result (.parquet) to {output_path}")
            pd.DataFrame.from_records(records).to_parquet(output_path)

    def execute(self, args):
        super().execute(args)

        client = KystdataClient()
        credentials = Credentials()

        client.login(
                username=credentials.user,
                password=credentials.password,
                csrf_token=credentials.csrf_token
        )

        records = [record for record in self._lookup_records(client, args) if record is not None]

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.lookup == 'incidents':
            self._save_incidents(records, args, output_dir)
        else:
            self._save_records(records, args, output_dir)

        client.logout()
