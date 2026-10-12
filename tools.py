"""Tools: what the model sees (schemas) and what actually runs (functions)."""
from datetime import datetime
from zoneinfo import ZoneInfo
import json
from pathlib import Path
import rules

# --- The data: the fake CRM/CDP ---
DATA_DIR = Path(__file__).parent / "data"
CUSTOMERS_FILE = DATA_DIR / "customers.json" # This is the fake CRM/CDP
CUSTOMERS = json.loads(CUSTOMERS_FILE.read_text())

# --- Fake order managment system ---
ORDERS_FILE = DATA_DIR / "orders.json"
ORDERS = json.loads(ORDERS_FILE.read_text())

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
    
    # In this demo we just tell the customer/agent that the request was received.
    # Real implementation would check the email address against the CRM/CDP 
    # and send a password reset link if it is registered.

    return {
        "request_received": True,
        "email": address,
        "message": "A password reset link was sent to this address if it is registered on a Bookly account.",
    }

def verify_customer(customer_id, customer_email, session):
    # This is a lightweight id check to verify the customer. Demo level.

    # No mid-session id switching allowed in this demo.
    if session.get("customer_id"): 
        return{"error": "already verified"}
    
    # Cleaning up the input
    customer_id = customer_id.strip().upper()
    customer_email = customer_email.strip().lower()

    # Look up the customer in the CRM/CDP - using customer_id as key
    customer_from_crm = CUSTOMERS.get(customer_id)

    # Check if the customer id existed in CRM and was linked to the email from the user input
    if customer_from_crm and customer_from_crm.get("email") == customer_email:
        # We have verification - Populate the session object
        session["customer_id"] = customer_id
        session ["customer_fname"] = customer_from_crm.get("fname")
        return {"verified": True, "name": customer_from_crm["name"]}
    
    # No verification - return False
    return {"verified": False}
    
def get_my_orders(session):
    # Return all orders belonging to the verified customer.
    # This works fine for the demo, we should not scan all orders and
    # we should not return all orders since the beginning of time
    # This is very much a read only fuction 
    customer_id = session.get("customer_id") # get who is asking from the session object
    if not customer_id:
        return {"error": "not_verified"}

    # Pick the orders where the customer_id on the order matches the customer_id of the session
    my_orders = {} 
    for order_id, order in ORDERS.items():
        if order["customer_id"] == customer_id:
            my_orders[order_id] = order
    return {"orders": my_orders}

def request_return(order_id, session):
    """Start a change-of-mind return for one of the verified customer's orders."""
    order_id = order_id.strip().upper()
    if not session.get("customer_id"):
        return {"error": "not_verified"}
    order = find_my_order(order_id, session)
    if order is None:
        return {"error": "order_not_found"}

    allowed, explanation = rules.can_return(order)
    if not allowed:
        return {"return_created": False, "reason": explanation}

    order["status"] = "return_requested"
    return {
        "return_created": True,
        "return_number": "R-" + order_id,
        "refund_sek": rules.refund_amount(order),
    }

def cancel_order(order_id, session):
    """Cancel one of the verified customer's orders, if it hasn't shipped yet."""
    order_id = order_id.strip().upper()
    if not session.get("customer_id"):
        return {"error": "not_verified"}
    order = find_my_order(order_id, session)
    if order is None:
        return {"error": "order_not_found"}

    allowed, explanation = rules.can_cancel(order)
    if not allowed:
        return {"cancelled": False, "reason": explanation}

    order["status"] = "cancelled"
    return {"cancelled": True}

def find_my_order(order_id, session):
    """Return the order if it belongs to the verified customer, otherwise None."""
    # Helper function - not a tool
    order = ORDERS.get(order_id)
    if order and order["customer_id"] == session.get("customer_id"):
        return order
    return None

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
    {
        "name": "verify_customer",
        "description": "Verify the customer by their customer_id and email address. "
                       "Call this before answering anything about the customer's orders, returns or cancellations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer's ID. e.g. C-007 or similar",
                },
                "customer_email": {
                    "type": "string",
                    "description": "The email address the customer says is on their Bookly account.",
                },
            },
            "required": ["customer_id", "customer_email"],
        },
    },
    {
        "name": "get_my_orders",
        "description": "Get all orders for the verified customer, with status, items, "
                   "delivery details and tracking. The customer must be verified first.",
         "input_schema": {"type": "object", "properties": {}}, # API requires an object. Even if it's an empty one
    }, 
    {
    "name": "request_return",
    "description": "Start a change-of-mind return for one of the verified customer's "
                   "orders. Only call after they have confirmed. Do not use this for "
                   "damaged, wrong or faulty items; those need a support specialist.",
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "Order ID, e.g. BK-1043"},
        },
        "required": ["order_id"],
    },
},
{
    "name": "cancel_order",
    "description": "Cancel one of the verified customer's orders. Only call after the "
                   "customer has confirmed they want to cancel.",
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "Order ID, e.g. BK-1050"},
        },
        "required": ["order_id"],
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
        if name == "verify_customer":
            return verify_customer(args.get("customer_id"), args.get("customer_email"), session)
        if name == "get_my_orders":
            return get_my_orders(session)
        if name == "request_return":
            return request_return(args["order_id"], session)
        if name == "cancel_order":
            return cancel_order(args["order_id"], session)
        return {"error": "unknown_tool", "tool": name}
    except Exception as e:
        return {"error": "tool_failed", "detail": str(e)}