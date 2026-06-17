"""Repository layer for the desktop application.

Provides a standardized database access layer using raw SQL with
connection-scoped transactions.
"""

from lab_system.app.database.connection import connection_scope


class BaseRepository:
    """Base repository with standard CRUD operations using raw SQL."""

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

    def execute_many(self, sql: str, params_list: list[tuple]) -> int:
        with connection_scope() as conn:
            count = 0
            for params in params_list:
                conn.execute(sql, params)
                count += 1
            return count

    def count(self, sql: str, params: tuple = ()) -> int:
        with connection_scope() as conn:
            row = conn.execute(sql, params).fetchone()
            return row[0] if row else 0

    def exists(self, sql: str, params: tuple = ()) -> bool:
        return self.count(sql, params) > 0
