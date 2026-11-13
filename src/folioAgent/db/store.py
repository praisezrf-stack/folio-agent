
import psycopg
from ..config import require_env


def get_db_connect():
    return psycopg.connect(require_env("PG_DSN"))