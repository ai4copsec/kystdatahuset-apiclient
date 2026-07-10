import base64
import datetime as dt
import json
import logging
from pathlib import Path

import platformdirs
import requests
from tqdm import tqdm

from .config import DATE_FORMAT, Impact, ReportType

logger = logging.getLogger(__name__)

APICLIENT_NAME = "kystdata"
BASE_URL = "https://kystdatahuset.no/ws/api"

class KystdataClient:
    login_url: str
    session: requests.Session

    access_token: str
    refresh_token: str
    csrf_token: str

    _cache_dir: Path

    def __init__(self, base_url: str = HOZINT_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

        self.session.headers.update({
            "accept": "application/json",
            "Content-Type": "application/json"
            "User-Agent": "Python-Secure-MMSI-Client/1.0",
        })

        self.access_token = None
        self.refresh_token = None
        self.csrf_token = None

        self.cache_dir = platformdirs.user_cache_path(appname=APICLIENT_NAME, ensure_exists=True)

    def login(self, email, password, csrf_token):
        """
        Authenticates with Kystdatahuset and saves the returned JWT bearer token.
        """
        url = f"{self.base_url}/auth/login/"

        # Add the specific CSRF token for this request
        headers = {"X-CSRFTOKEN": csrf_token}
        self.csrf_token = csrf_token

        payload = {
            "email": email,
            "password": password
        }

        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()  # Raises an error for 4xx or 5xx responses

            logger.info(f"{APICLIENT_NAME} Login successful")
            data = response.json()

            try:
                token_data = response.json()
                token = (
                    token_data.get("data")['JWT']
                    if isinstance(token_data, dict)
                    else response.text
                )
            except ValueError:
                token = response.text.strip().strip('"')

            if not token:
                logger.warning(f"{Failed to parse token from login response. {token=}")
                return False

            # Update session headers with the Bearer token for future calls
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

            logger.info("Successfully authenticated and obtained JWT token.")
            return True

        except requests.exceptions.HTTPError as err:
            raise RuntimeError(f"{APICLIENT_NAME} Authentication / Login failed: {err}")

    def lookup_ship(self, value: any, key: str = 'mmsi', ) -> dict | None:
        """Resolves an MMSI number using the authenticated session."""
        url = f"{self.base_url}/ship/combined/{key}/{value}"
        try:
            response = self.session.get(url, timeout=10)

            # Handle token expiration (HTTP 401 Unauthorized)
            if response.status_code == 401:
                print("Token expired or unauthorized. Attempting re-login...")
                if self.login():
                    # Retry the exact request one time after successful re-auth
                    response = self.session.get(url, timeout=10)
                else:
                    return None

            response.raise_for_status()
            msg = response.json()
            if 'data' in msg:
                return msg['data']
            else:
                return None
        except requests.RequestException as e:
            print(f"Data lookup error: {e}")
            return None

    def lookup_ship_mmsi(self, mmsi: str | int) -> dict | None:
        return self.lookup_ship(key='mmsi', value=mmsi)

    def lookup_ship_callsign(self, callsign: str | int) -> dict | None:
        return self.lookup_ship_(key='callsign', value=callsign)

    def lookup_incident(self, from_time: dt.datetime, to_time: dt.datetime):
        url = f"{self.base_url}/kystinfo/norvts-incidents"
        try:
            response = self.session.get(url, timeout=10)

            # Handle token expiration (HTTP 401 Unauthorized)
            if response.status_code == 401:
                print("Token expired or unauthorized. Attempting re-login...")
                if self.login():
                    # Retry the exact request one time after successful re-auth
                    response = self.session.get(url, timeout=10)
                else:
                    return None

            response.raise_for_status()
            msg = response.json()
            if 'data' in msg:
                return msg['data']
            else:
                return None
        except requests.RequestException as e:
            print(f"Data lookup error: {e}")
            return None

