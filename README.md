# Bookly Support Agent

A conversational AI agent for customer support at **Bookly**, a fictional online bookstore. The goal: customers ask about orders, returns and store policies in plain language, and the agent understands the request, asks for missing information, uses tools to look up data or take actions, and answers.

This is an early-stage prototype, built step by step. The current version is the foundation: a working agent loop with multi-turn conversation, running in the terminal. Tools come next.

## Design principles

The architecture rests on one idea: **the LLM handles language, code handles rules.**

- The model understands what the customer wants, decides what it needs, and writes the reply.
- The model will never execute anything itself. It *requests* tool calls; Python code decides what actually runs and what data comes back.
- Business rules, permissions and anything involving customer data are enforced in code, not in the prompt.

Some deliberate choices follow from this:

- **No agent framework.** The orchestration loop is written by hand in `agent.py`. At this scale, owning the loop gives full control over guardrails, logging and error handling, and keeps the behavior easy to follow. A framework such as LangGraph becomes worth its weight with long-running workflows, human approval steps or multiple coordinated agents.
- **Swappable model.** All model calls go through one function in `llm.py`. Changing model or provider means changing one file.
- **Interface-independent agent.** The agent is a function that takes a conversation and returns a reply. The CLI, a future web UI and automated tests all call the same function.
- **State separated by trust.** What was said and what is true are kept apart from the start (see *Conversation state* below), so verification and permissions can be added without restructuring.

## Current capabilities

- Interactive chat in the terminal
- Multi-turn conversation: the agent remembers everything said earlier in the conversation
- Safety cap on the number of model calls per customer turn, with a fallback message

The agent does not yet have tools or Bookly-specific data, so it answers from general knowledge. Questions about specific orders or policies will get generic answers until those steps are added.

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
| "Do you ship to Norway?" | A friendly but generic answer, since Bookly's policies aren't loaded yet |

## How the agent loop works

The LLM is stateless: every API call is independent, and the model can only read text and return text. Agent behavior comes from a loop in `agent.py`:

1. Send the system prompt and the full conversation so far to the model.
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
│   └── system.md       # System prompt: the agent's role and tone
├── requirements.txt    # Python dependencies
└── .env.example        # Template for configuration
```

## Roadmap

- [x] Agent loop with multi-turn memory
- [ ] Order status lookup tool, against mock order data
- [ ] Customer verification enforced in code, using `session`
- [ ] Returns and refunds, with eligibility rules in plain Python
- [ ] Store policies (shipping, returns) and password reset
- [ ] Escalation to a human agent with a conversation summary
- [ ] Logging of every step for observability and auditing
- [ ] Web chat interface with a live view of tool calls and agent state
- [ ] Evaluation suite: scripted conversations with pass/fail checks

## Known limitations

- No tools or Bookly data yet; answers are generic.
- Conversation history grows without limit; long conversations get gradually more expensive. A production version would summarize or trim older turns.
- API errors (wrong key, no credit, network issues) are not yet handled gracefully and will stop the program.
