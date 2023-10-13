"""
Main module for the application.
This module imports the necessary functions from db.py and executes them.
"""

import argparse
import os
import sys

import autogen
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

TERMINATION_KEYWORD = "APPROVED"

COMPLETION_PROMPT = "If everything looks good, respond with " + TERMINATION_KEYWORD

USER_PROXY_PROMPT = (
    """
    A human admin. Interact with the Product Manager to discuss the plan.
    Plan execution needs to be approved by this admin.
    """
    + COMPLETION_PROMPT
)

DATA_ENGINEER_PROMPT = (
    """
    A Data Engineer. You follow an approved plan.
    Generate the initial SQL query based on the requirements
    provided by. Send it to the Senior Data Analyst for review.
    """
    + COMPLETION_PROMPT
)

SENIOR_DATA_ANALYST_PROMPT = (
    """
    Senior data analyst. You follow an approved plan.
    You run the SQL query, generate the response,
    and send it to the Product Manager for final review.
    """
    + COMPLETION_PROMPT
)

PRODUCT_MANAGER_PROMPT = (
    """Product Manager. Validate the response to make sure it is correct. """
    + COMPLETION_PROMPT,
)


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
            "use_cache": False,
            "temperature": 0,
            "config_list": autogen.config_list_from_models(["gpt-4"]),
            "request_timeout": 120,
            "functions": [
                {
                    "name": "run_sql",
                    "description": "Run a SQL query against the postgres database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "The SQL query to run",
                            }
                        },
                        "required": ["sql"],
                    },
                }
            ],
        }

        # build the function map
        function_map = {"run_sql": db.run_sql}

        # Create our terminame msg function
        def is_termination_msg(content):
            have_content = content.get("content", None) is not None
            if have_content and TERMINATION_KEYWORD in content["content"]:
                return True
            return False

        # Create a set of agents with specific roles
        # Admin user proxy agent - takes in the prompt and manages the group chat
        user_proxy = autogen.UserProxyAgent(
            name="Admin",
            llm_config=gpt4_config,
            human_input_mode="NEVER",
            system_message=USER_PROXY_PROMPT,
            code_execution_config=False,
            is_termination_msg=is_termination_msg,
        )

        # data engineer agent - generates the sql query
        data_engineer = autogen.AssistantAgent(
            name="Data_Engineer",
            llm_config=gpt4_config,
            human_input_mode="NEVER",
            system_message=DATA_ENGINEER_PROMPT,
            code_execution_config=False,
            is_termination_msg=is_termination_msg,
        )

        # product manager - validate the response to make sure it is correct
        senior_data_analyst = autogen.AssistantAgent(
            name="Senior_Data_Analyst",
            llm_config=gpt4_config,
            human_input_mode="NEVER",
            system_message=SENIOR_DATA_ANALYST_PROMPT,
            code_execution_config=False,
            is_termination_msg=is_termination_msg,
            function_map=function_map,
        )

        # senior data analyst agent - tun the sql query and generate the response
        product_manager = autogen.AssistantAgent(
            name="Product_Manager",
            llm_config=gpt4_config,
            human_input_mode="NEVER",
            system_message=PRODUCT_MANAGER_PROMPT,
            code_execution_config=False,
            is_termination_msg=is_termination_msg,
        )

        # create a group chat and initiate the chat
        groupchat = autogen.GroupChat(
            agents=[
                user_proxy,
                data_engineer,
                senior_data_analyst,
                product_manager,
            ],
            messages=[],
            max_round=10,
        )
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt4_config)

        user_proxy.initiate_chat(manager, clear_history=True, message=prompt)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)
