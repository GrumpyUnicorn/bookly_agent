"""The agent loop. Knows nothing about the UI: it takes the conversation and
returns a reply, so a CLI, a web UI or an eval script can all call it."""
from pathlib import Path
from llm import call_llm

SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text()
MAX_STEPS = 5  # safety cap so a confused model can never loop forever
FALLBACK = "Sorry, I couldn't complete that. Let me connect you with a colleague."


def text_of(response):
    """Pull the plain text out of the model's reply."""
    return "".join(block.text for block in response.content if block.type == "text")


def run_turn(history, session):
    """Handle one customer turn. `history` is the full conversation (it grows
    across turns). `session` will hold facts our code controls (e.g. verified
    customer) - unused in step 1, but in place so nothing needs rewiring later."""
    for step in range(MAX_STEPS):
        response = call_llm(SYSTEM_PROMPT, history)
        history.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":  # model wrote a reply: turn done
            return text_of(response)
        # Step 2 adds tool handling here.

    return FALLBACK
