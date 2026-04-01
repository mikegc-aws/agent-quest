"""
Agent Quest - AI-Powered Tabletop RPG Games Master

A complete agent with dice rolling, rule book lookup, and player state tracking,
powered by Amazon Bedrock via the Strands Agents SDK.

Requirements:
    uv add strands-agents

Setup:
    - Configure AWS credentials (aws configure / aws sso login)
    - Ensure Amazon Nova Lite is enabled in Amazon Bedrock

Usage:
    uv run agent.py
"""

import random

from strands import Agent, tool
from strands.models import BedrockModel


# ---------------------------------------------------------------------------
# Custom output handler - colors tool calls and hides thinking text
# ---------------------------------------------------------------------------

DIM = "\033[2m"
BOLD = "\033[1m"
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
                # Haven't found closing tag yet, keep buffering
                break
        else:
            start = _buffer.find("<thinking>")
            if start != -1:
                # Print everything before the tag, then enter thinking mode
                _flush_safe(_buffer[:start])
                _inside_thinking = True
                _buffer = _buffer[start + len("<thinking>"):]
            elif "<" in _buffer:
                # Might be a partial tag starting, hold back from the < onward
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
# Tool 1: Dice Rolling
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
# Tool 2: Rule Book Lookup
# ---------------------------------------------------------------------------

@tool
def lookup_rule(topic: str) -> str:
    """Look up rules from the game's rule book.

    Args:
        topic: The topic to search for (e.g. 'combat', 'magic', 'skill checks')
    """
    with open("rulebook.txt", "r") as f:
        content = f.read()

    topic_lower = topic.lower()
    sections = content.split("## ")
    for section in sections:
        if topic_lower in section.lower():
            return f"📖 Rule Book - {section.strip()}"

    return f"📖 No rules found for '{topic}'."


# ---------------------------------------------------------------------------
# Tool 3 & 4: Player State
# ---------------------------------------------------------------------------

player = {
    "name": "Adventurer",
    "hp": 20,
    "max_hp": 20,
    "strength": 3,
    "spell_slots": 3,
    "inventory": ["rusty sword", "leather armor", "10 gold coins"],
}


@tool
def get_player_state() -> str:
    """Get the current state of the player character including HP, inventory, and abilities."""
    return (
        f"🧙 {player['name']}\n"
        f"   HP: {player['hp']}/{player['max_hp']}\n"
        f"   Strength Modifier: +{player['strength']}\n"
        f"   Spell Slots: {player['spell_slots']}\n"
        f"   Inventory: {', '.join(player['inventory'])}"
    )


@tool
def update_player_state(
    hp_change: int = 0,
    add_item: str = "",
    remove_item: str = "",
    use_spell_slot: bool = False,
) -> str:
    """Update the player's state after an event.

    Args:
        hp_change: Amount to change HP by (positive for healing, negative for damage)
        add_item: An item to add to inventory
        remove_item: An item to remove from inventory
        use_spell_slot: Whether to consume a spell slot
    """
    changes = []

    if hp_change != 0:
        player["hp"] = max(0, min(player["max_hp"], player["hp"] + hp_change))
        direction = "healed" if hp_change > 0 else "took damage"
        changes.append(
            f"{direction} ({hp_change:+d} HP, now {player['hp']}/{player['max_hp']})"
        )

    if add_item:
        player["inventory"].append(add_item)
        changes.append(f"gained '{add_item}'")

    if remove_item:
        if remove_item in player["inventory"]:
            player["inventory"].remove(remove_item)
            changes.append(f"lost '{remove_item}'")

    if use_spell_slot:
        if player["spell_slots"] > 0:
            player["spell_slots"] -= 1
            changes.append(f"used a spell slot ({player['spell_slots']} remaining)")
        else:
            changes.append("no spell slots remaining!")

    return f"📋 Updated: {', '.join(changes)}" if changes else "📋 No changes made."


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

model = BedrockModel(model_id="us.amazon.nova-lite-v1:0")

agent = Agent(
    model=model,
    system_prompt="""You are a dramatic and entertaining tabletop RPG games master.

Your responsibilities:
- Narrate scenes vividly and with atmosphere
- Use dice rolls to determine the outcomes of actions involving chance
- Consult the rule book when you need to know game mechanics
- Track the player's state (HP, inventory, spell slots) and update it after events
- Always check the player's current state before making decisions about their abilities

Game rules:
- A d20 roll of 15+ is generally a success for skill checks
- Always look up specific rules in the rule book rather than making them up
- Apply damage and healing by updating the player's state
- Be fair but dramatic. Make every roll feel consequential""",
    tools=[roll_dice, lookup_rule, get_player_state, update_player_state],
    callback_handler=game_callback,
)

# Set the scene, then start the game loop
agent("Set the scene. I'm a wandering adventurer arriving at a small village at dusk.")

while True:
    user_input = input(f"\n{BOLD}You > {RESET}")
    if user_input.lower() in ("quit", "exit"):
        print("Thanks for playing!")
        break
    agent(user_input)
