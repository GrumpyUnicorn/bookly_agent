"""Tools: what the model sees (schemas) and what actually runs (functions)."""
from datetime import datetime
from zoneinfo import ZoneInfo


# --- The tool functions: what actually runs ---

def get_current_time():
    """Return the current date and time in Sweden.
    Sweden was selected just because I am based here.
    The LLM is not aware of time, and a lot of questions are related to time."""
    now = datetime.now(ZoneInfo("Europe/Stockholm"))
    return {
        "date": now.strftime("%Y-%m-%d"),
        "weekday": now.strftime("%A"),
        "time": now.strftime("%H:%M"),
        "timezone": "Swedish time (Europe/Stockholm)",
    }


# --- The tool menu: what the model sees.
#                    In the format Anthropic's Messages API expects. ---

TOOL_SCHEMAS = [
    {
        "name": "get_current_time",
        "description": "Get the current date, weekday and time in Sweden. Call this before "
                       "answering anything that depends on today's date or the current time, "
                       "such as delivery dates, shipping cutoffs or support hours.",
        "input_schema": {"type": "object", "properties": {}},
    }
]


# --- The dispatcher: connects a tool name to its function ---

TOOL_FUNCTIONS = {"get_current_time": get_current_time}


def execute_tool(name, args, session):
    """Run the requested tool. Always returns a result, never crashes."""
    try:
        if name == "get_current_time":
            return get_current_time()
        return {"error": "unknown_tool", "tool": name}
    except Exception as e:
        return {"error": "tool_failed", "detail": str(e)}