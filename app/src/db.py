import psycopg2
from psycopg2 import sql


class PostgresManager:
    """
    Class to manage interactions with a PostgreSQL database.
    """
    def __init__(self):
        """
        Initialize the PostgresManager with no connection or cursor.
        """
        self.conn = None
        self.cursor = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def connect_with_url(self, url):
        """
        Connect to the PostgreSQL database using the provided URL.
        """
        self.conn = psycopg2.connect(url)
        self.cursor = self.conn.cursor()

    def upsert(self, table_name, _dict):
        columns = _dict.keys()
        values = [sql.Placeholder(k) for k in columns]

        # Define the SET clause for updating the existing row
        assignments = sql.SQL(", ").join(
            sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder(k))
            for k in columns
        )

        query = sql.SQL(
            "INSERT INTO {table} ({columns}) VALUES ({values}) "
            "ON CONFLICT (id) DO UPDATE SET {assignments}"
        ).format(
            table=sql.Identifier(table_name),
            columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
            values=sql.SQL(", ").join(values),
            assignments=assignments,
        )

        self.cursor.execute(query, _dict)
        self.conn.commit()

    def delete(self, table_name, _id):
        self.cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (_id,))
        self.conn.commit()

    def get(self, table_name, _id):
        self.cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (_id,))
        return self.cursor.fetchone()

    def get_all(self, table_name):
        self.cursor.execute(f"SELECT * FROM {table_name}")
        return self.cursor.fetchall()

    def run_sql(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def get_table_definition(self, table_name):
        # Fetch columns and their types
        self.cursor.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
        """,
            (table_name,),
        )
        columns = self.cursor.fetchall()

        # Construct the CREATE TABLE statement
        column_definitions = [f"{col[0]} {col[1]}" for col in columns]
        ddl = (
            "CREATE TABLE "
            + table_name
            + " (\n  "
            + ",\n  ".join(column_definitions)
            + "\n);"
        )

        return ddl

    def get_all_table_names(self):
        self.cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """
        )
        return [row[0] for row in self.cursor.fetchall()]

    def get_table_definitions_for_prompt(self):
        table_names = self.get_all_table_names()
        definitions = []
        for table_name in table_names:
            definitions.append(self.get_table_definition(table_name))
        return "\n".join(definitions)
