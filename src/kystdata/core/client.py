import datetime as dt
import logging
from pathlib import Path

import platformdirs
import requests

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

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

        self.session.headers.update(
            {
                "accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Python-Secure-MMSI-Client/1.0",
            }
        )

        self.access_token = None
        self.refresh_token = None
        self.csrf_token = None
        self._login_credentials: dict[str, str] | None = None

        self.cache_dir = platformdirs.user_cache_path(appname=APICLIENT_NAME, ensure_exists=True)

    def login(self, username: str, password: str, csrf_token: str) -> bool:
        """
        Authenticates with Kystdatahuset and saves the returned JWT bearer token.
        """
        url = f"{self.base_url}/auth/login/"

        headers = {"X-CSRFTOKEN": csrf_token}
        self.csrf_token = csrf_token
        self._login_credentials = {"username": username, "password": password, "csrf_token": csrf_token}

        payload = {
            "username": username,
            "password": password
        }

        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            token_data = response.json()
            token = token_data.get("data", {}).get("JWT") if isinstance(token_data, dict) else None

            if not token:
                raise RuntimeError("Failed to parse token from login response")

            self.access_token = token
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

            logger.info("%s login successful", APICLIENT_NAME)
            return True

        except requests.exceptions.HTTPError as err:
            raise RuntimeError(f"{APICLIENT_NAME} Authentication / Login failed: {err}")

    def logout(self) -> None:
        """
        Clears the local session state. The Kystdatahuset API does not expose a
        logout endpoint, so this only drops the locally held tokens and credentials.
        """
        self.session.headers.pop("Authorization", None)
        self.access_token = None
        self.refresh_token = None
        self._login_credentials = None
        logger.info("%s logout", APICLIENT_NAME)

    def _retry_once_on_unauthorized(self, response: requests.Response, request_fn):
        if response.status_code != 401:
            return response
        if not self._login_credentials:
            return response
        self.login(**self._login_credentials)
        return request_fn()

    def _response_data(self, response: requests.Response):
        response.raise_for_status()
        msg = response.json()
        if isinstance(msg, dict) and "data" in msg:
            return msg["data"]
        return msg

    def lookup_ship(self, value: any, key: str = 'mmsi') -> dict | None:
        """Resolves a ship record using the authenticated session."""
        url = f"{self.base_url}/ship/combined/{key}/{value}"
        try:
            def request_fn():
                return self.session.get(url, timeout=10)

            response = self._retry_once_on_unauthorized(request_fn(), request_fn)
            return self._response_data(response)
        except requests.RequestException as e:
            logger.error("Data lookup error: %s", e)
            return None

    def lookup_ship_mmsi(self, mmsi: str | int) -> dict | None:
        return self.lookup_ship(key='mmsi', value=mmsi)

    def lookup_ship_callsign(self, callsign: str | int) -> dict | None:
        return self.lookup_ship(key='callsign', value=callsign)

    def lookup_norvts_incidents(
        self,
        from_time: dt.datetime | None = None,
        to_time: dt.datetime | None = None,
    ) -> list[dict] | dict | None:
        url = f"{self.base_url}/kystinfo/norvts-incidents"

        payload: dict[str, str] = {}
        if from_time is not None:
            payload["startTime"] = from_time.isoformat()
        if to_time is not None:
            payload["endTime"] = to_time.isoformat()

        try:
            def request_fn():
                return self.session.post(url, json=payload or None, timeout=10)

            response = self._retry_once_on_unauthorized(request_fn(), request_fn)
            return self._response_data(response)
        except requests.RequestException as e:
            logger.error("Data lookup error: %s", e)
            return None

    lookup_incident = lookup_norvts_incidents
    get_incidents = lookup_norvts_incidents
