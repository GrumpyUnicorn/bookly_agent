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

def show_response(step, response):
    """Print everything in one model response (verbose mode)."""
    usage = response.usage
    print(f"\n  ── step {step + 1} · stop: {response.stop_reason} · "
          f"tokens in/out: {usage.input_tokens}/{usage.output_tokens}")
    for block in response.content:
        if block.type == "thinking":
            print(f"  [thinking]     {block.thinking or '(not shown)'}")
        elif block.type == "text":
            print(f"  [text]         {block.text}")
        elif block.type == "tool_use":
            print(f"  [tool request] {block.name} {block.input}")

def run_turn(history, session, verbose=False):
    """Handle one customer turn and return the agent's reply.

    `history` is the full conversation; it grows across turns.
    `session` holds facts only code controls, such as the verified customer.
    With verbose=True, every model step and tool result is printed.
    """
    for step in range(MAX_STEPS):
        response = call_llm(SYSTEM_PROMPT, history, tools.TOOL_SCHEMAS)  # Calls wrapper
        history.append({"role": "assistant", "content": response.content}) #response content to history
        if verbose:
            show_response(step, response)

        # Anything other than a tool request is the final reply to the customer.
        if response.stop_reason != "tool_use":
            return text_of(response) # helper function that grabs the text 

        # The model requested tools
        tool_results = []
        for block in response.content:  # iterate through the response content
            if block.type == "tool_use":  # if the block is a tool use
                result = tools.execute_tool(block.name, block.input, session) # execute the tool
                if verbose:
                    print(f"  [tool result]  {result}")
                tool_results.append({ # add the result to the tool results list
                    "type": "tool_result",
                    "tool_use_id": block.id,   # links the result to its request
                    "content": json.dumps(result), # convert the result to a JSON string
                })

        # Send the results back to the model in the next step.
        history.append({"role": "user", "content": tool_results}) # add the tool results to the history

    return FALLBACK
