import json
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

from kystdata.cli.base import BaseParser
from kystdata.core.client import KystdataClient
from kystdata.core.config import Credentials

logger = logging.getLogger(__name__)

class RawParser(BaseParser):
    """
    :param parser: The base parser
    """

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser=parser)

        parser.description = "kystdata raw -- perform a raw query against an arbitrary API endpoint"

        parser.add_argument("endpoint", type=str,
                            help="Endpoint path, relative to the API base url, e.g. 'kystinfo/norvts-incidents'")
        parser.add_argument("--method", type=str, default="GET",
                            choices=["GET", "POST", "PUT", "PATCH", "DELETE"], help="HTTP method, default: %(default)s")
        parser.add_argument("--param", action="append", default=[], metavar="KEY=VALUE",
                            help="Query string parameter, can be given multiple times")
        parser.add_argument("--data", type=str, default=None,
                            help="JSON request body: a literal JSON string, '@<file>' to read from a file, "
                                 "or '-' to read from stdin")
        parser.add_argument("--output", type=str, default=None,
                            help="File to write the (JSON) response to, default: print to stdout")

    def _load_payload(self, data: str | None) -> dict | list | None:
        if data is None:
            return None
        if data == "-":
            return json.load(sys.stdin)
        if data.startswith("@"):
            return json.loads(Path(data[1:]).read_text(encoding="utf-8"))
        return json.loads(data)

    def execute(self, args):
        super().execute(args)

        client = KystdataClient()
        credentials = Credentials()

        client.login(
                username=credentials.user,
                password=credentials.password,
                csrf_token=credentials.csrf_token
        )

        params = dict(param.split("=", 1) for param in args.param) if args.param else None
        payload = self._load_payload(args.data)

        result = client.request(
            endpoint=args.endpoint,
            method=args.method,
            params=params,
            json_payload=payload,
        )

        text = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(text, encoding="utf-8")
            logger.info(f"Saved response to {output_path}")
        else:
            print(text)

        client.logout()
