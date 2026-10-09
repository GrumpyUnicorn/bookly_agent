# Bookly Support Agent

A conversational AI agent for customer support at **Bookly**, a fictional online bookstore. The goal: customers ask about orders, returns and store policies in plain language, and the agent understands the request, asks for missing information, uses tools to look up data or take actions, and answers.

This is an early-stage prototype, built step by step. The current version has a working agent loop with multi-turn conversation and a knowledge layer with Bookly's store policies, running in the terminal. Tools come next.

## Design principles

The architecture rests on one idea: **the LLM handles language, code handles rules.**

- The model understands what the customer wants, decides what it needs, and writes the reply.
- The model will never execute anything itself. It *requests* tool calls; Python code decides what actually runs and what data comes back.
- Business rules, permissions and anything involving customer data are enforced in code, not in the prompt.

Some deliberate choices follow from this:

- **No agent framework.** The orchestration loop is written by hand in `agent.py`. At this scale, owning the loop gives full control over guardrails, logging and error handling, and keeps the behavior easy to follow. A framework such as LangGraph becomes worth its weight with long-running workflows, human approval steps or multiple coordinated agents.
- **Swappable model.** All model calls go through one function in `llm.py`. Changing model or provider means changing one file.
- **Interface-independent agent.** The agent is a function that takes a conversation and returns a reply. The CLI, a future web UI and automated tests all call the same function.
- **Knowledge separated from behavior.** How the agent behaves (`prompts/system.md`) and what it knows about Bookly (`knowledge/policies.md`) live in separate files, as they would have different owners in a real deployment. The agent answers policy questions only from the knowledge, and says so when the answer isn't there.
- **State separated by trust.** What was said and what is true are kept apart from the start (see *Conversation state* below), so verification and permissions can be added without restructuring.

## Current capabilities

- Interactive chat in the terminal
- Multi-turn conversation: the agent remembers everything said earlier in the conversation
- Answers about shipping, returns, refunds and accounts, grounded in Bookly's policies
- Admits when information isn't in the policies instead of guessing, and offers a specialist
- Short, direct replies
- Safety cap on the number of model calls per customer turn, with a fallback message

The agent does not yet have tools, so it cannot look up orders, start returns or check the current date. It is instructed never to claim it has done any of these things.

## Getting started

**Requirements:** Python 3.10 or newer, and an Anthropic API key with credit.

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# then edit .env and add your key

# 4. Run the agent
python cli.py
```

Type your messages at the `You:` prompt. Type `quit` to exit.

### Configuration (`.env`)

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `MODEL` | Model to use (default: `claude-haiku-5-5`, a fast, low-cost model) |

`.env` is excluded from version control. Never commit API keys.

## Try this

| You say | What to expect |
|---|---|
| "Hi, my name is Anna." then "What's my name?" | The agent remembers: the full conversation is sent on every call |
| "Do you ship to Norway?" | Standard shipping only, 4–7 business days, 99 SEK |
| "Can I return an e-book?" | No, not once downloaded, unless the file is faulty |
| "Do you sell gift cards?" | Not covered by the policies, so the agent says it doesn't know and offers a specialist |
| "Can you send me a password reset link?" | Explains the "Forgot password" option, without claiming to send anything |

## How the agent loop works

The LLM is stateless: every API call is independent, and the model can only read text and return text. Agent behavior comes from a loop in `agent.py`:

1. Send the system prompt (behavior instructions plus Bookly's policies) and the full conversation so far to the model.
2. If the model replies with text, the turn is done: return the reply to the customer.
3. *(Next step)* If the model requests a tool, the code runs it, appends the result to the conversation, and goes back to step 1.

Step 3 is where one customer *turn* can involve several model *steps*, for example "look up order, then answer." The loop is already structured for this and stops after `MAX_STEPS` with a fallback message, so a confused model can never loop forever.

### Conversation state

Two pieces of state follow each conversation:

- **`history`** — what was *said*: every customer message and model reply (and, once tools exist, every tool request and result). It is sent to the model on every call and is the model's only memory.
- **`session`** — what is *true*: facts controlled only by code, such as which customer has been verified. It is never sent to the model, and the model cannot change it. It is passed through the agent now, unused, so verification can be added without rewiring.

## Project structure

```
bookly-agent/
├── cli.py              # Command-line chat: reads input, calls the agent, prints replies
├── agent.py            # The agent loop: model calls and step limit
├── llm.py              # Thin wrapper around the LLM API (the only provider-specific file)
├── prompts/
│   └── system.md       # System prompt: role, style, and how to use the knowledge
├── knowledge/
│   └── policies.md     # Bookly's store policies: shipping, returns, refunds, accounts
├── requirements.txt    # Python dependencies
└── .env.example        # Template for configuration
```

## Knowledge

`knowledge/policies.md` holds Bookly's (fictional) store policies. At startup, `agent.py` appends it to the system prompt inside `<knowledge>` tags, so the full policies are available on every call. With a knowledge base this small, including everything is simpler than retrieval and can't miss anything. At larger scale, the knowledge layer would move to retrieval (search over a help center), while the rest of the architecture stays the same.

## Roadmap (tentative)

- [x] Agent loop with multi-turn memory
- [x] Knowledge layer with store policies
- [ ] Tool handling in the loop, starting with a current-time tool
- [ ] Order status lookup tool, against mock order data
- [ ] Customer verification enforced in code, using `session`
- [ ] Returns and refunds, with eligibility rules in plain Python
- [ ] Password reset link (mocked action)
- [ ] Escalation to a human agent with a conversation summary
- [ ] Logging of every step for observability and auditing
- [ ] Web chat interface with a live view of tool calls and agent state
- [ ] Evaluation suite: scripted conversations with pass/fail checks

## Known limitations

- No tools yet: the agent can't look up orders or take actions, and doesn't know the current date, so it can't turn delivery times into actual dates.
- Conversation history grows without limit; long conversations get gradually more expensive. A production version would summarize or trim older turns.
- API errors (wrong key, no credit, network issues) are not yet handled gracefully and will stop the program.