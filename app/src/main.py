"""
Main module for the application.
This module imports the necessary functions from db.py and executes them.
"""

import argparse
import os
import sys

from autogen import AssistantAgent
from autogen import config_list_from_json
from autogen import config_list_from_models
from autogen import GroupChat
from autogen import GroupChatManager
from autogen import UserProxyAgent
from dotenv import load_dotenv
import llm

from db import PostgresManager

# load .env file
load_dotenv()

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
    This function parses the command line arguments, connects to the database,
    retrieves table definitions, constructs and sends a prompt to the OpenAI API,
    and executes the returned SQL query.
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

        # Build the gpt_configuration object

        # Build the function map

        # Create our terminame msg function

        # Create a set of agents with specific roles
        # Admin user proxy agent - takes in the prompt and manages the group chat
        # data engineer agent - generates the sql query
        # senior data analyst agent - tun the sql query and generate the response
        # product manager - validate the response to make sure it is correct

        # create a group chat and initiate the chat


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)
