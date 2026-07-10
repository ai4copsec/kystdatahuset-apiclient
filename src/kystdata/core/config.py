from __future__ import annotations

import datetime as dt
import importlib
import uuid
from enum import Enum
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

DATE_FORMAT = "%Y-%m-%d"

LOG_FORMAT = '[{asctime}][{levelname:^8s}] {name}: {message}'
LOG_STYLE = '{'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

class Credentials(BaseSettings):
    user: str
    password: str

    csrf_token: str = Field(default=str(uuid.uuid4()))

    model_config = SettingsConfigDict(
                    env_file='.env',
                    env_nested_delimiter='__',
                    env_prefix='KYSTDATA_APICLIENT_',
                    extra='ignore'
                )

class Incident(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    incident_id: int = Field(alias="id")
    lng: float = Field(description="Longitude")
    lat: float = Field(description="Latitude")

    hendelsesid: str | None = Field(default=None)
    hendelsetype: str | None = Field(default=None)
    dato: str | None = Field(default=None)

    skipstype: str | None = Field(default=None)
    storrelse_bt: int | None = Field(default=None, description="Size in BRT")
    merknad: str | None = Field(default=None, description="Comments on context")
    registrert_av: str | None = Field(default=None, description="Registered by / Source")

    link_news: str | None = Field(default=None, description="Link in news")
    media_4_admin: str | None = Field(default=None, description="Internal use")
    open_media: str | None = Field(default=None)
    
    vindretning: str | None = Field(default=None, description="Direction of wind")
    vindstyrke: int | None = Field(default=None, description="Strenght of wind")
    mmsi: int
    imo: int | None = Field(default=None, description="IMO Number")
    ship_name: str | None = Field(default=None)
    skipstype_skipsregister: str | None = Field(default=None)



    @classmethod
    def get_dataframe(cls, incidents: list[Incident]) -> pd.DataFrame:
        columns = cls.model_fields.keys()
        return pd.DataFrame.from_records([dict(x) for x in incidents], columns=columns)


    @classmethod
    def get_annotated_dataframe(cls, incidents: list[Incident]):
        df = cls.get_dataframe(incidents=incidents)

        if not importlib.util.find_spec('damast'):
            raise RuntimeError("Please install 'damast' to support using AnnotatedDataFrame")

        import polars
        from damast.core.dataframe import AnnotatedDataFrame
        pdf = polars.from_pandas(df)

        metadata = AnnotatedDataFrame.infer_annotation(pdf)
        return AnnotatedDataFrame(pdf, metadata)



