"""The agent loop. Knows nothing about the UI: it takes the conversation and
returns a reply, so a CLI, a web UI or an eval script can all call it."""
from pathlib import Path
from llm import call_llm
import tools
import json
BASE_DIR = Path(__file__).parent

SYSTEM_PROMPT = (
    (BASE_DIR / "prompts" / "system.md").read_text()
    + "\n\n<knowledge>\n"
    + (BASE_DIR / "knowledge" / "policies.md").read_text()
    + "\n</knowledge>"
)

MAX_STEPS = 5  # safety cap so a confused model can never loop forever
FALLBACK = "Sorry, I couldn't complete that. Let me connect you with a colleague."


def text_of(response):
    """Pull the plain text out of the model's reply."""
    return "".join(block.text for block in response.content if block.type == "text")


def run_turn(history, session):
    """Handle one customer turn. `history` is the full conversation (it grows
    across turns). `session` will hold facts our code controls (e.g. verified
    customer)."""
    for step in range(MAX_STEPS):
        response = call_llm(SYSTEM_PROMPT, history, tools.TOOL_SCHEMAS)
        history.append({"role": "assistant", "content": response.content})

        # Everything that is not a tool call is a reply that should be forwarded to the user.
        if response.stop_reason != "tool_use":  # model wrote a reply: turn done
            return text_of(response)
        
        # Ok, let's handle tool use.
        tool_results = [] # An empty list to store the results of the tool calls.
        for block in response.content:
            if block.type == "tool_use":
                result = tools.execute_tool(block.name, block.input, session)

                # Debug info - how did the tool interaction go? (remove later)
                print(f"  [tool] {block.name} {block.input} -> {result}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,     # links the result to its request
                    "content": json.dumps(result),
                })

        history.append({"role": "user", "content": tool_results})   # then loop again

    return FALLBACK
