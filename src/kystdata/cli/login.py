import logging
from argparse import ArgumentParser

from kystdata.cli.base import BaseParser
from kystdata.core.client import KystdataClient
from kystdata.core.config import Credentials

logger = logging.getLogger(__name__)

class LoginParser(BaseParser):
    """
    :param parser: The base parser
    """

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser=parser)

        parser.description = "kystdata login -- authenticate and display the bearer token"

    def execute(self, args):
        super().execute(args)

        client = KystdataClient()
        credentials = Credentials()

        client.login(
                username=credentials.user,
                password=credentials.password,
                csrf_token=credentials.csrf_token
        )

        print(client.access_token)

        client.logout()
