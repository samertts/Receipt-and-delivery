from lab_system.app.database.connection import connection_scope


class BaseRepository:
    def fetch_one(self, sql: str, params: tuple = ()):
        with connection_scope() as conn:
            return conn.execute(sql, params).fetchone()

    def fetch_all(self, sql: str, params: tuple = ()):
        with connection_scope() as conn:
            return conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple = ()):
        with connection_scope() as conn:
            cur = conn.execute(sql, params)
            return cur.lastrowid
