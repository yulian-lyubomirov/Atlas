from __future__ import annotations

from contextlib import contextmanager
from enum import Enum
from typing import Any, Iterable

import pandas as pd
import psycopg
import configparser


class FetchFormat(str, Enum):
    record = "record"
    json = "json"
    dataframe = "dataframe"


class DB:
    def __init__(self) -> None:
        self._conn: psycopg.Connection | None = None

    @property
    def conn(self) -> psycopg.Connection:
        if self._conn is None:
            raise psycopg.errors.InterfaceError("No connection to database")
        return self._conn

    def connect(
        self,
        *,
        conninfo: str | None = None,
        service: str | None = None,
        config_file: str | None = None,
        **kwargs,
    ) -> "DB":
        if conninfo is None and service is None and config_file is None:
            raise ValueError("Either 'conninfo' or 'service' must be provided")
        if service:
            conninfo = f"service={service}"
        if config_file:
            conninfo = self.conninfo_from_config(path=config_file, section="atlasdb")

        self._conn = psycopg.Connection.connect(
            conninfo=conninfo, autocommit=True, **kwargs
        )
        return self

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @contextmanager
    def cursor(self, *args, **kwargs):
        cur = self.conn.cursor(*args, **kwargs)
        try:
            yield cur
        finally:
            cur.close()

    def execute(self, query: str, params: dict | None = None) -> None:
        with self.cursor() as cur:
            cur.execute(query, params)

    def fetch(self, query: str, params: dict | None = None) -> list[tuple]:
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def fetch_one(self, query: str, params: dict | None = None) -> tuple | None:
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetch_df(self, query: str, params: dict | None = None) -> pd.DataFrame:
        with self.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            cols = [c.name for c in cur.description]
        return pd.DataFrame(rows, columns=cols)

    def copy_df(self, *, df: pd.DataFrame, table: str, schema: str = "public") -> int:
        # Fast + safe for bulk inserts. Uses CSV, no manual quoting hacks.
        full_table = f"{schema}.{table}"
        with self.cursor() as cur:
            with cur.copy(
                f"COPY {full_table} ({', '.join(df.columns)}) FROM STDIN WITH (FORMAT csv, HEADER false)"
            ) as cp:
                cp.write(df.to_csv(index=False, header=False))
        return len(df)

    @staticmethod
    def conninfo_from_config(*, path: str, section: str) -> str:
        cfg = configparser.ConfigParser()

        if not cfg.read(path):
            raise FileNotFoundError(f"Config file not found: {path}")

        if section not in cfg:
            raise KeyError(f"Section [{section}] not found in {path}")

        db = cfg[section]

        required = {"host", "port", "dbname", "user", "password"}
        missing = required - set(db)
        if missing:
            raise KeyError(f"Missing keys in [{section}]: {', '.join(missing)}")

        return " ".join(
            f"{k}={db[k]}" for k in ("host", "port", "dbname", "user", "password")
        )
