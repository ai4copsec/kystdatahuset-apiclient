import datetime as dt
import logging
import tempfile
from argparse import ArgumentParser
from pathlib import Path

from tqdm import tqdm

from kystdata.cli.base import BaseParser
from kystdata.core.client import KystdataClient
from kystdata.core.config import (
    DATE_FORMAT,
    Credentials,
    Impact,
    Report,
    ReportType,
)

logger = logging.getLogger(__name__)

class QueryParser(BaseParser):
    """
    :param parser: The base parser
    """

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser=parser)

        parser.description = "kystdata query"

        parser.add_argument("--from-time", type=str, help="Starting date in the format YYYY-mm-dd")
        parser.add_argument("--to-time", type=str, help="End date in the format YYYY-mm-dd")

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

    def execute(self, args):
        super().execute(args)

        client = KystdataClient()
        credentials = Credentials()

        client.login(
                email=credentials.user,
                password=credentials.password,
                csrf_token=credentials.csrf_token
        )

        from_time = None
        if args.from_time:
            from_time = dt.datetime.strptime(args.from_time, DATE_FORMAT)

        to_time = None
        if args.to_time:
            to_time = dt.datetime.strptime(args.to_time, DATE_FORMAT)

        incidents = client.get_incidents(from_time=from_time,
                                     to_time=to_time,
                    )
                    #                 longitude=args.at_lon,
                    #                 latitude=args.at_lat,
                    #                 radius=args.radius,
                    #                 region=args.region,
                    #                 country=args.country,
                    #                 category=args.category,
                    #                 report_id=args.report_id,
                    #                 report_type=args.report_type,
                    #                 verified=args.verified,
                    #                 max_pages=args.max_pages
                    #                 )

        if args.output_dir:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        if args.output_format == 'json':
            logger.info(f"Saving reports (.json) in {str(output_dir)}")
            for r in tqdm(reports, desc="Report:"):
                report = Report(**r)
                report.save_json(output_dir=output_dir)
        elif args.output_format == 'parquet':
            logger.info(f"Saving all incidents (.parquet) in {str(output_dir)}")
            adf = Report.get_annotated_dataframe([Report(**x) for x in reports])
            adf.export(output_dir / "kystdata-incidents.parquet")

        client.logout()
