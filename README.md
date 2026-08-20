# Agent Quest

AI-powered tabletop RPG games master built with the [Strands Agents SDK](https://github.com/strands-agents/sdk-python) and [Amazon Bedrock](https://aws.amazon.com/bedrock/).

Code samples for the blog post: [Build Your First AI Agent with AWS Free Tier](https://mikegchambers.com/blog/build-first-ai-agent-aws-free-tier/)

## What's in here

| File | Description |
|---|---|
| `agent_simple.py` | Minimal agent using a local Ollama model, demonstrates the core concepts |
| `agent.py` | Full agent with Bedrock, rule book lookup, and player state tracking |
| `rulebook.txt` | Game rules the agent consults during play |

## Quick Start (Local Model)

```bash
# Install dependencies
uv sync

# Pull a local model
ollama pull llama3.1

# Run the simple agent
uv run agent_simple.py
```

## Quick Start (AWS Bedrock)

```bash
# Install dependencies
uv sync

# Configure AWS credentials
aws configure  # or: aws sso login

# Run the full agent
uv run agent.py
```

Type your actions at the `You >` prompt. Type `quit` to exit.

## Trying Different Models

`agent.py` uses `us.amazon.nova-2-lite-v1:0` by default. Change the `model_id`
to try different Bedrock models:

```python
# Amazon Nova Micro (cheapest, text-only)
model = BedrockModel(model_id="us.amazon.nova-micro-v1:0")

# Anthropic Claude Haiku (fast, strong reasoning)
model = BedrockModel(model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0")
```

> **Note:** Nova 2 models are only callable through a cross-region inference
> profile — use the `us.` prefix. The bare `amazon.nova-2-lite-v1:0` returns a
> `ValidationException`.

## License

MIT
