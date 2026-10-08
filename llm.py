"""Thin wrapper around the LLM API. The rest of the code only calls call_llm(),
so switching model or provider later means changing this one file."""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # reads ANTHROPIC_API_KEY and MODEL from .env
MODEL = os.getenv("MODEL", "claude-haiku-5-5")
_client = Anthropic()


def call_llm(system, messages, tools=None):
    kwargs = dict(model=MODEL, max_tokens=1024, system=system, messages=messages)
    if tools:  # only send a tool menu if we have tools
        kwargs["tools"] = tools
    return _client.messages.create(**kwargs)
