"""
Simple AI Agent - Tabletop RPG Games Master

A minimal agent that demonstrates the core concepts:
- A model (the brain)
- A tool (the hands)
- A system prompt (the personality)

This version uses a local Ollama model. See agent.py for the
full version with AWS Bedrock and additional tools.

Requirements:
    uv add 'strands-agents[ollama]'
    ollama pull llama3.1
"""

import random

from strands import Agent, tool
from strands.models.ollama import OllamaModel


# ---------------------------------------------------------------------------
# Custom output handler - colors tool calls and hides thinking text
# ---------------------------------------------------------------------------

DIM = "\033[2m"
RESET = "\033[0m"

_buffer = ""
_inside_thinking = False


def _flush_safe(text):
    """Print text that definitely doesn't contain thinking tags."""
    if text:
        print(text, end="", flush=True)


def game_callback(**kwargs):
    """Custom callback that styles tool calls and suppresses thinking text."""
    global _buffer, _inside_thinking

    # Skip reasoning text from extended thinking
    if kwargs.get("reasoningText"):
        return

    # Show tool calls in dim text
    tool_use = kwargs.get("event", {}).get("contentBlockStart", {}).get("start", {}).get("toolUse")
    if tool_use:
        print(f"\n{DIM}  ↳ {tool_use['name']}{RESET}", end="", flush=True)

    data = kwargs.get("data", "")
    complete = kwargs.get("complete", False)

    if data:
        _buffer += data

    # Process the buffer, flushing what we can
    while True:
        if _inside_thinking:
            end = _buffer.find("</thinking>")
            if end != -1:
                _inside_thinking = False
                _buffer = _buffer[end + len("</thinking>"):]
            else:
                break
        else:
            start = _buffer.find("<thinking>")
            if start != -1:
                _flush_safe(_buffer[:start])
                _inside_thinking = True
                _buffer = _buffer[start + len("<thinking>"):]
            elif "<" in _buffer:
                lt = _buffer.rfind("<")
                _flush_safe(_buffer[:lt])
                _buffer = _buffer[lt:]
                break
            else:
                _flush_safe(_buffer)
                _buffer = ""
                break

    # On completion, flush anything remaining
    if complete:
        if not _inside_thinking:
            _flush_safe(_buffer)
        _buffer = ""
        _inside_thinking = False
        if kwargs.get("data"):
            print("\n")


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

@tool
def roll_dice(sides: int, count: int = 1) -> str:
    """Roll dice and return the results.

    Args:
        sides: Number of sides on each die (e.g. 6 for a standard die, 20 for a d20)
        count: How many dice to roll
    """
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls)
    if count == 1:
        return f"🎲 Rolled a d{sides}: {rolls[0]}"
    return f"🎲 Rolled {count}d{sides}: {rolls} (Total: {total})"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

# Choose a model - this is the "brain" of the agent
model = OllamaModel(host="http://localhost:11434", model_id="llama3.1")

# Create the agent with a system prompt (the "personality") and tools (the "hands")
agent = Agent(
    model=model,
    system_prompt="""You are a dramatic and entertaining tabletop RPG games master.
You narrate scenes vividly and use dice rolls to determine outcomes.
When a player attempts an action that involves chance, roll appropriate dice
and narrate the result. A d20 roll of 15 or higher is generally a success.
Keep responses concise but atmospheric.""",
    tools=[roll_dice],
    callback_handler=game_callback,
)

agent("I kick open the tavern door and stride up to the bar. 'Barkeep! Your finest ale!'")
