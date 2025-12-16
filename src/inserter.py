from abc import ABC, abstractmethod
from contextlib import contextmanager
import pandas as pd

import psycopg
from psycopg import sql
from enum import Enum


class FetchFormat(str, Enum):
    record = "record"
    json = "json"
    dataframe = "dataframe"


class AbstractDB(ABC):
    # _instance = None

    # def __new__(cls, *args, **kwargs):
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)
    #     return cls._instance
    def __init__(self, debug: bool = False) -> None:
        self._conn = None

    @property
    def conn(self) -> psycopg.AsyncConnection | psycopg.Connection:
        if self._conn is None:
            raise psycopg.errors.InterfaceError("No connection to database")
        return self._conn

    @abstractmethod
    def connect(self):
        pass

    def _base_copy_to_table(
        self,
        table_name: str,
        schema: str = None,
        df: pd.DataFrame = None,
        csv: str = None,
        columns: list[str] = None,
        delimiter="\t",
    ):
        if df is None and csv is None:
            raise ValueError("Either df or csv must be provided")

        if schema:
            table_name = f"{schema}.{table_name}"

        if df is not None:
            csv = df.to_csv(
                index=False, header=False, sep=delimiter, quotechar="🖯"
            ).replace("🖯", "$🖯$")
            columns = df.columns.tolist()
            rows = len(df)
        else:
            rows = len(csv.split("\n")) - 1

        if columns:
            columns_str = f"({', '.join(columns)})"
        else:
            columns_str = ""

        query = f"""COPY {table_name}{columns_str} FROM STDIN  
                        WITH 
                            NULL AS '' 
                            DELIMITER E'{delimiter}'
                """
        return csv, query, rows

    def _base_insert_from_table(self, source, target, on_conflict, columns, pkeys):
        if on_conflict not in ["ignore", "update"]:
            raise ValueError("on_conflict must be either 'ignore' or 'update'")

        if "." in source:
            source_schema, source = source.split(".")
        if "." in target:
            target_schema, target = target.split(".")

        if on_conflict == "update":
            upd_values = sql.SQL(", ").join(
                sql.Composed(
                    [
                        sql.Identifier(k),
                        sql.SQL(" = "),
                        sql.SQL("EXCLUDED.{}").format(sql.Identifier(k)),
                    ]
                )
                for k in columns
                if k not in pkeys
            )
            pkeys_values = sql.SQL(" AND ").join(
                sql.Composed(
                    [
                        sql.Identifier(target_schema, target, k),
                        sql.SQL(" = "),
                        sql.SQL("EXCLUDED.{}").format(sql.Identifier(k)),
                    ]
                )
                for k in pkeys
            )
            conflict_res = sql.SQL("DO UPDATE SET {} WHERE {}").format(
                upd_values, pkeys_values
            )
        else:
            conflict_res = sql.SQL("DO NOTHING")

        query = sql.SQL(
            """
            INSERT INTO {target} SELECT * FROM {source} 
            ON CONFLICT ({pkeys}) {conflict_res}
        """
        ).format(
            target=sql.Identifier(target_schema, target),
            source=sql.Identifier(source_schema, source),
            pkeys=sql.SQL(", ").join(sql.Identifier(k) for k in pkeys),
            conflict_res=conflict_res,
        )
        return query


class AsyncDB(AbstractDB):
    def __enter__(self):
        raise RuntimeError("Use 'async with' instead of 'with'")

    def __exit__(self):
        pass

    async def __aenter__(self):
        # await self.connect()
        return self

    def __aexit__(self, exc_type, exc_value, traceback):
        self.close()

    def connect(self, conninfo: str = None, service: str = None, **kwargs):
        if conninfo is None and service is None:
            raise ValueError("Either 'conninfo' or 'service' must be provided")
        if service:
            conninfo = f"service={service}"

        self._conn = psycopg.Connection.connect(
            conninfo=conninfo, autocommit=True, **kwargs
        )
        return self

    def close(self):
        self.conn.close()

    @contextmanager
    def cursor(self, *args, **kwargs):
        cur = self.conn.cursor(*args, **kwargs)
        try:
            yield cur
        finally:
            cur.close()

    def execute(self, query: str, params=None, notice=False, *args, **kwargs):
        notice_msg = []
        if notice:

            def on_notice(notice):
                nonlocal notice_msg
                notice_msg.append(notice.message_primary)

            self.conn.add_notice_handler(on_notice)

        with self.cursor(*args, **kwargs) as cursor:
            cursor.execute(query, params=params)

        return notice_msg

    def copy_to_table(
        self,
        table_name: str,
        schema: str = None,
        df: pd.DataFrame = None,
        csv: str = None,
        columns: list[str] = None,
        delimiter="\t",
    ):
        csv, query, rows = self._base_copy_to_table(
            table_name, schema, df, csv, columns, delimiter
        )

        with self.cursor() as cursor:
            with cursor.copy(query) as copy:
                copy.write(csv)

        return rows


class Inserter:
    def __init__(
        self,
        db: AsyncDB = None,
        debug: bool = False,
        infer_tz: bool = False,
    ):
        if db is not None:
            self.conn = db
        else:
            self.conn = AsyncDB(debug=debug)

    def connect(self, *args, **kwargs):
        self.conn.connect(*args, **kwargs)
        return self

    def cursor(self):
        """Provides a synchronous database cursor."""
        return self.conn.cursor()

    def insert(
        self,
        table: str,
        schema: str = "public",
        df: pd.DataFrame = None,
        csv: str = None,
        columns: list[str] = None,
        # on_conflict: ON_CONFLICT = ON_CONFLICT.DO_NOTHING,
        # force_nulls: bool = False,
        # recompress_after: bool = True,
        # drop_duplicates: bool = True,
    ):
        """Inserts a dataframe into a table.

        Parameters
        ----------
        table : str
            Name of the table to insert into
        schema : str, optional
            Schema of the table, by default primarydata
        df : pd.DataFrame, optional
            Dataframe to insert. Columns must match the table columns. Mutually
            exclusive with `csv` and `columns` parameters.
        csv : str, optional
            String containing the CSV data to insert. Mutually
            exclusive with `df`
        columns : list, optional
            List of columns of the CSV to insert. If not provided, all columns will be
            inserted. Mutually exclusive with `df` and only valid when `csv` is provided
        on_conflict : ON_CONFLICT, optional
            What to do on conflict, possible values are:
            - 'do_nothing'
            - 'update'
            By default 'do_nothing'
        force_nulls : bool, optional
            If false, null values in the passed dataframe will be ignored when
            updating. If true, null values will be inserted into the database.
            By default False
        recompress_after : bool, optional
            If true, the table chunks will be recompressed after the insert.
            By default True
        drop_duplicates : bool, optional
            If true, duplicate rows will be dropped from the dataframe before
            inserting. By default True

        Returns
        -------
        int
            Number of rows inserted/updated
        """
        if df is None and csv is None:
            raise ValueError("Either df or csv must be provided")

        # on_conflict = ON_CONFLICT(on_conflict)

        # db_columns, pkeys = await self._get_columns_info(table, schema)

        # if on_conflict != ON_CONFLICT.DO_NOTHING and pkeys is None:
        #     raise ValueError(
        #         "Table must have primary keys defined to use 'update' on conflict"
        #     )  # ! Mover esto más arriba

        # if df is not None:
        #     df = self._prepare_dataframe(df, db_columns, pkeys, drop_duplicates)
        #     columns = df.columns.tolist()

        # if columns:
        #     self._check_columns(columns, db_columns, table)

        rows = self._insert_data(
            table=table,
            schema=schema,
            df=df,
            csv=csv,
            columns=columns,
            # pkeys=pkeys,
            # on_conflict=on_conflict,
            # force_nulls=force_nulls,
            # recompress_after=recompress_after,
        )
        return rows

    def _insert_data(
        self,
        table: str,
        schema: str,
        df: pd.DataFrame,
        csv: str,
        columns: list[str],
    ):
        """Insert data into the database"""
        rows = self.conn.copy_to_table(
            df=df, csv=csv, columns=columns, table_name=table, schema=schema
        )
        return rows

    def fetch(self, query: str, params=None, output: FetchFormat = "record"):
        """Fetch data from the database."""
        output = FetchFormat(output)
        with self.cursor() as cursor:  # Now `cursor()` is properly defined
            cursor.execute(query, params=params)
            data = cursor.fetchall()
            if output == "record":
                return data
            elif output == "json":
                columns = [c.name for c in cursor.description]
                return [dict(zip(columns, row)) for row in data]
            elif output == "dataframe":
                return pd.DataFrame(data, columns=[c.name for c in cursor.description])
