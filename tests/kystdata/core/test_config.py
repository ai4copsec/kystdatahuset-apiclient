import json
from kystdata.core.config import Incident


TEST_INCIDENT = '{"id":4849,"lng":8.5495,"lat":62.688166666667,"hendelsesid":null,"hendelsetype":"Fart\u00F8y i drift","dato":"2026-01-03","skipstype":"Bulkfart\u00F8y","storrelse_bt":24341,"merknad":"Fart\u00F8y fikk problemer med hovedmotor ved ankomst Sunndals\u00F8ra. ","registrert_av":"NOR VTS","link_news":"","media_4_admin":"eb9e1acf-7212-4a6f-af87-ee11ec86ebdf","vindretning":"S","open_media":"","vindstyrke":2,"mmsi":538009005,"imo":9607447,"ship_name":"HYDRA DAWN","skipstype_skipsregister":""}'


def test_incident():
    data = json.loads(TEST_INCIDENT)
    incident = Incident(**data)

    for k,v in data.items():
        if k != "id":
            assert getattr(incident, k) == v, f"{k=} == {v=}"

    a = Incident(**incident.model_dump())
    df = Incident.get_dataframe([a])






