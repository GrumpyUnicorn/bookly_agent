"""Minimal command-line chat. Only job: read input, call run_turn, print reply."""
from agent import run_turn

history, session = [], {}
print("Bookly support - type 'quit' to exit\n")

while True:
    user = input("You: ").strip()
    if user.lower() in {"quit", "exit"}:
        break
    if not user:
        continue
    history.append({"role": "user", "content": user})
    print(f"Agent: {run_turn(history, session)}\n")
