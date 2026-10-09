"""Thin wrapper around the LLM API. The rest of the code only calls call_llm(),
so switching model or provider later means changing this one file."""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # reads ANTHROPIC_API_KEY and MODEL from .env
MODEL = os.getenv("MODEL", "claude-haiku-5-5") # claude-haiku-5-5 is the default model
_client = Anthropic() # client is the Anthropic API client (to be used from this file only)


def call_llm(system, messages, tools=None):
    """Calls to LLM is stateless, so we pass the system prompt (from system.md)
    and the whole message history (user questions and llm answers) every time. 
    
    Later, when we add tools, we pass a list of tools (as dictionaries) via the `tools` parameter.
    The Anthropic message API includes 'native tool use'.
    """
    kwargs = dict(model=MODEL, max_tokens=1024, system=system, messages=messages)
    if tools:  # only send a tool menu if we have tools
        kwargs["tools"] = tools
    return _client.messages.create(**kwargs) # ** just unpacks the dict into the function arguments
