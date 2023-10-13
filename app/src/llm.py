"""
Purpose:
    Interact with the OpenAI API.
    Provide supporting prompt engineering functions.
"""

import os
from typing import Any, Dict

from dotenv import load_dotenv
import openai

# load .env file
load_dotenv()

assert os.environ.get("OPENAI_API_KEY")

# get openai api key
openai.api_key = os.environ.get("OPENAI_API_KEY")


def safe_get(data, dot_chained_keys):
    """
    Safely get a value from a nested dictionary or list using dot notation.
    For example, given the dictionary {'a': {'b': [{'c': 1}]}},
    safe_get(data, 'a.b.0.c') will return 1.
    """
    keys = dot_chained_keys.split(".")
    for key in keys:
        try:
            if isinstance(data, list):
                data = data[int(key)]
            else:
                data = data[key]
        except (KeyError, TypeError, IndexError):
            return None
    return data


def response_parser(response: Dict[str, Any]):
    return safe_get(response, "choices.0.message.content")


def prompt(prompt: str, model: str = "gpt-4") -> str:
    """
    Send a prompt to the OpenAI API and return the response.
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response_parser(response)


def add_cap_ref(
    prompt: str, prompt_suffix: str, cap_ref: str, cap_ref_content: str
) -> str:
    """
    Attaches a capitalized reference to the prompt.

    Example
        prompt = 'Refactor this code.'
        prompt_suffix = 'Make it more readable using this EXAMPLE.'
        cap_ref = 'EXAMPLE'
        cap_ref_content = 'def foo():\n
            return True'

        returns
        'Refactor this code. Make it more readable using this EXAMPLE.\n
        \n
        EXAMPLE\n
        \n
        def foo():\n
            return True'
    """

    new_prompt = f"""{prompt} {prompt_suffix}\n\n{cap_ref}\n\n{cap_ref_content}"""

    return new_prompt
