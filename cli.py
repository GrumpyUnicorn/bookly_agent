"""Minimal command-line chat. Only job: read input, call run_turn, print reply."""
from agent import run_turn

# history is the message history (user questions and llm answers)
# session is the session state (e.g. the conversation id)
history, session = [], {}
print("Bookly support - type 'quit' to exit\n")

while True:
    customer_message = input("You: ").strip()
    if customer_message.lower() in {"quit", "exit"}:
        break
    if not customer_message: #empty line - ask again
        continue
    history.append({"role": "user", "content": customer_message})
    print(f"Agent: {run_turn(history, session)}\n")
