import psycopg
from ..config import require_env
from dataclasses import dataclass
from typing import Any


@dataclass
class DB_client:
    def connect(self):
        return psycopg.connect(require_env("PG_DSN"))

    def execute(self, sql, query=None) -> list[tuple[Any, ...]]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, query)
                if cur.description is not None:
                    return cur.fetchall()
            return []

    def executemany(self, sql, query, returning: bool = False) -> list:
        result = []
        if not query:
            return []

        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, query, returning=returning)
                if returning:
                    while True:
                        res = cur.fetchall()
                        result.extend(res)
                        if not cur.nextset():
                            break

        return result

    def fetch_one(self, sql, query):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, query)
                return cur.fetchone()


db_server = DB_client()
