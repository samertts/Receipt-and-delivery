from contextlib import contextmanager
from lab_system.app.database import db as _db


@contextmanager
def connection_scope():
    with _db.get_conn() as conn:
        yield conn
