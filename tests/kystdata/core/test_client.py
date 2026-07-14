import datetime as dt

from kystdata.core.client import KystdataClient


class DummyResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class DummySession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.headers = {}
        self.calls = []

    def post(self, url, json=None, timeout=None, headers=None):
        self.calls.append(("post", url, json, headers, timeout))
        response = self.responses.pop(0)
        return response

    def get(self, url, timeout=None):
        self.calls.append(("get", url, timeout))
        response = self.responses.pop(0)
        return response

    def request(self, method, url, params=None, json=None, timeout=None):
        self.calls.append(("request", method, url, params, json, timeout))
        response = self.responses.pop(0)
        return response


def test_lookup_norvts_incidents_posts_time_window():
    client = KystdataClient()
    client.session = DummySession([DummyResponse(payload={"data": [{"id": 1}]})])

    result = client.lookup_norvts_incidents(
        from_time=dt.datetime(2026, 1, 1, 0, 0, 0),
        to_time=dt.datetime(2026, 1, 31, 23, 59, 59),
    )

    assert result == [{"id": 1}]
    method, url, payload, headers, timeout = client.session.calls[0]
    assert method == "post"
    assert url.endswith("/kystinfo/norvts-incidents")
    assert payload == {
        "startTime": "2026-01-01T00:00:00",
        "endTime": "2026-01-31T23:59:59",
    }
    assert timeout == 10


def test_request_performs_raw_query_against_arbitrary_endpoint():
    client = KystdataClient()
    client.session = DummySession([DummyResponse(payload={"data": {"mmsi": 257123456}})])

    result = client.request(
        endpoint="/ship/combined/mmsi/257123456",
        method="get",
        params={"foo": "bar"},
    )

    assert result == {"mmsi": 257123456}
    method, http_method, url, params, json_payload, timeout = client.session.calls[0]
    assert method == "request"
    assert http_method == "GET"
    assert url.endswith("/ship/combined/mmsi/257123456")
    assert params == {"foo": "bar"}
    assert json_payload is None
    assert timeout == 10


def test_lookup_ships_for_mmsis_posts_mmsi_list():
    client = KystdataClient()
    client.session = DummySession([DummyResponse(payload={"data": [{"mmsi": 477125300}]})])

    result = client.lookup_ships_for_mmsis(["477125300"])

    assert result == [{"mmsi": 477125300}]
    method, http_method, url, params, json_payload, timeout = client.session.calls[0]
    assert method == "request"
    assert http_method == "POST"
    assert url.endswith("/ship/for-mmsis")
    assert json_payload == {"mmsiIds": [477125300]}
    assert timeout == 10

