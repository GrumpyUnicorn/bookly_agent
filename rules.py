"""Bookly's business rules: the decisions the agent is never allowed to make itself.

WHY THESE RULES LIVE IN CODE
----------------------------
The language model understands the customer and explains decisions, but it does
not make them. Every action tool (request_return, cancel_order) calls the
functions in this file before doing anything, and does what they decide,
regardless of what the model believes. There are two reasons:

1. The model can be tricked. Customers can argue, plead or try to manipulate it:
   "your colleague already approved this", "it's only two days late",
   "ignore your instructions". A model can be talked into agreeing.
   This code cannot. The same order always gets the same decision.

2. The model is bad at calculations. Counting 30 days across months, comparing
   dates or adding up refunds are exactly the things language models get wrong.
   Python gets them right every time.

So the model *asks*, and this code *decides*. If the model calls request_return
for an order that isn't eligible, the tool refuses, and the explanation returned
by these functions goes back to the model so it can tell the customer why.

HOW THE RULE FUNCTIONS WORK
---------------------------
Each rule function returns two values: (allowed, explanation).
- allowed:     True or False, the decision.
- explanation: a short sentence saying why, which the model uses to explain
               the decision to the customer.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --- Policy values --------------------------------------------------------
# These numbers must match knowledge/policies.md 

RETURN_WINDOW_DAYS = 30   # printed books can be returned this many days after delivery
RETURN_FEE_SEK = 49       # deducted from the refund when the customer changed their mind


# --- Helpers --------------------------------------------------------------

def today():
    """Today's date in Sweden, where Bookly operates.

    Used for the return window. Using Swedish time, not the computer's local
    time, means the decision is the same wherever the agent is running.
    """
    return datetime.now(ZoneInfo("Europe/Stockholm")).date()


# --- Rules ----------------------------------------------------------------

def can_return(order):
    """Decide whether an order can be returned.

    Rules (see "Returns and refunds" in policies.md):
    - Only delivered orders can be returned.
    - E-books cannot be returned once downloaded.
    - Printed books can be returned within RETURN_WINDOW_DAYS of delivery.

    Returns (allowed, explanation).
    """
    if order["status"] != "delivered":
        return False, "Only delivered orders can be returned."

    for item in order["items"]:
        if item["format"] == "ebook":
            return False, "E-books can't be returned once downloaded."

    delivered = datetime.fromisoformat(order["delivered_date"]).date()
    last_day = delivered + timedelta(days=RETURN_WINDOW_DAYS)
    if today() > last_day:
        return False, f"The return window ended on {last_day}."

    return True, f"Returnable until {last_day}."


def can_cancel(order):
    """Decide whether an order can be cancelled.

    Rule (see "Changing or cancelling an order" in policies.md):
    - An order can be cancelled until it has shipped, which means only while
      its status is "processing". After that, it can be returned instead.

    Returns (allowed, explanation).
    """
    if order["status"] == "processing":
        return True, "The order hasn't shipped yet."
    return False, "Orders can only be cancelled before they ship."


def refund_amount(order):
    """Calculate the refund for a change-of-mind return, in SEK.

    This demo tool only handles change-of-mind returns, so RETURN_FEE_SEK is
    always deducted. Damaged or wrong items are handed to a specialist.

    Calculated here, never by the model, because it involves money.
    """
    total = 0
    for item in order["items"]:
        total += item["price_sek"]
    return total - RETURN_FEE_SEK