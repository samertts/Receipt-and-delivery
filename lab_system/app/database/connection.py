from contextlib import contextmanager
from lab_system.app.database.db import get_conn


@contextmanager
def connection_scope():
    with get_conn() as conn:
        yield conn
