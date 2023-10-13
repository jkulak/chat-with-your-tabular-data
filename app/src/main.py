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
        gpt4_config = {
            "seed": 42,  # change the seed for different trials
            "temperature": 0,
            "config_list": config_list_gpt4,
            "request_timeout": 120,
        }

        # Create our terminame msg function
        # This function is not defined in the example, so we'll leave it as a placeholder
        # terminame_msg_function = ...

        # Create a set of agents with specific roles
        # Admin user proxy agent - takes in the prompt and manages the group chat
        user_proxy = autogen.UserProxyAgent(
            name="Admin",
            system_message="A human admin. Interact with the planner to discuss the plan. Plan execution needs to be approved by this admin.",
            code_execution_config=False,
        )

        # data engineer agent - generates the sql query
        engineer = autogen.AssistantAgent(
            name="Engineer",
            llm_config=gpt4_config,
            system_message="""Engineer. You follow an approved plan. You write python/shell code to solve tasks. Wrap the code in a code block that specifies the script type. The user can't modify your code. So do not suggest incomplete code which requires others to modify. Don't use a code block if it's not intended to be executed by the executor.
            Don't include multiple code blocks in one response. Do not ask others to copy and paste the result. Check the execution result returned by the executor.
            If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
            """,
        )

        # senior data analyst agent - tun the sql query and generate the response
        scientist = autogen.AssistantAgent(
            name="Scientist",
            llm_config=gpt4_config,
            system_message="""Scientist. You follow an approved plan. You are able to categorize papers after seeing their abstracts printed. You don't write code.""",
        )

        # product manager - validate the response to make sure it is correct
        planner = autogen.AssistantAgent(
            name="Planner",
            system_message="""Planner. Suggest a plan. Revise the plan based on feedback from admin and critic, until admin approval.
            The plan may involve an engineer who can write code and a scientist who doesn't write code.
            Explain the plan first. Be clear which step is performed by an engineer, and which step is performed by a scientist.
            """,
            llm_config=gpt4_config,
        )

        # create a group chat and initiate the chat
        groupchat = autogen.GroupChat(
            agents=[user_proxy, engineer, scientist, planner],
            messages=[],
            max_round=50,
        )
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt4_config)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)
