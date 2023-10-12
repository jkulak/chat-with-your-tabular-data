"""
Main module for the application.
This module imports the necessary functions from db.py and executes them.
"""

import argparse
import os
import sys

from dotenv import load_dotenv
import llm

from db import PostgresManager

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


POSTGRES_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"
TABLE_RESPONSE_FORMAT_CAP_REF = "TABLE_RESPONSE_FORMAT"

PROMPT_DATABASE_VERSION = "Postgres "

SQL_DELIMITER = "--------"


def main() -> None:
    """
    Main function to execute the necessary functions.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prompt", help="Prompt for the OpenAI API", default="NO_PROMPT"
    )
    args = parser.parse_args()

    if args.prompt == "NO_PROMPT":
        print("Error: No prompt provided.")
        print("Usage: python main.py --prompt PROMPT")
        sys.exit(1)

    prompt = args.prompt

    with PostgresManager() as db:
        db.connect_with_url(DB_URL)

        table_definitions = db.get_table_definitions_for_prompt()

        # print("prompt v1", prompt)
        # print("table definitions", table_definitions)

        prompt = llm.add_cap_ref(
            prompt,
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query.:",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            table_definitions,
        )

        # print("prompt v2", prompt)

        prompt = llm.add_cap_ref(
            prompt,
            f"""\n\nRespond in this format {TABLE_RESPONSE_FORMAT_CAP_REF}.
            Keep the delimiter {SQL_DELIMITER} between description and the sql
            Make the SQL query below {SQL_DELIMITER} executable as is by the database.
            """,
            TABLE_RESPONSE_FORMAT_CAP_REF,
            f"""<explanation of the sql query>
{SQL_DELIMITER}
<here the sql query exclusively as raw text, so it can be executed>""",
        )

        # print("prompt v3", prompt)

        prompt_response = llm.prompt(prompt)
        print("🥫 prompt_response", prompt_response)

        sql_query = prompt_response.split(SQL_DELIMITER)[1].strip()
        # print("🥗 query", sql_query)

        result = db.run_sql(sql_query)
        print(result)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)
