"""Minimal command-line chat. Only job: read input, call run_turn, print reply."""
from agent import run_turn
import sys
VERBOSE = "--verbose" in sys.argv or "--debug" in sys.argv

# history is the message history (user questions and llm answers)
# session is the session state (the name and id when a customer has been verified)
history, session = [], {}
print("Bookly support - type 'quit' to exit\n")

while True:
    # After verifcation, use the customer's name in the prompt (Use "You" otherwise)
    # This might be overkill, but it shows how we use the session object
    fname = session.get("customer_fname")
    prompt = f"{fname} (verified)" if fname else "You"
    customer_message = input(f"{prompt}: ").strip()

    # Exit conversation with 'quit' or 'exit'
    if customer_message.lower() in {"quit", "exit"}:
        break
    if not customer_message: #empty line - ask again
        continue
    history.append({"role": "user", "content": customer_message})
    print(f"Agent: {run_turn(history, session, VERBOSE)}\n")
