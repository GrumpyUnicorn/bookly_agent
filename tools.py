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


def send_password_reset(email):
    """Mock sending a password reset link to the registered account email.
    Never accepts, sets, or returns a password — code enforces that, not the prompt."""
    address = (email or "").strip()
    if not address or "@" not in address:
        return {"error": "invalid_email", "detail": "A valid email address is required."}
    
    # This is where we would actually send the password reset link to the email address.
    # We would fist check if the email address is registered on a Bookly account.
    # For now, everything is happy path.
    
    return {
        "sent": True,
        "email": address,
        "message": "A password reset link was sent to this address if it is registered on a Bookly account.",
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
    },
    {
        "name": "send_password_reset",
        "description": "Send a password reset link to the email address registered on the "
                       "customer's Bookly account. Call this after the customer asks for a "
                       "reset and has given that email. Never ask for or set a password; "
                       "the link can only go to the registered address.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "The email address the customer says is on their Bookly account.",
                },
            },
            "required": ["email"],
        },
    },
]

# --- The dispatcher: connects a tool name to its function ---
# This lets agent.py call a tool/function by name, passing arguments and session.
def execute_tool(name, args, session):
    """Run the requested tool. Always returns a result, never crashes."""
    try:
        if name == "get_current_time":
            return get_current_time()
        if name == "send_password_reset":
            return send_password_reset(args.get("email", ""))
        return {"error": "unknown_tool", "tool": name}
    except Exception as e:
        return {"error": "tool_failed", "detail": str(e)}