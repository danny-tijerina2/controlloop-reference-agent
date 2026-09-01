"""A three-agent support desk.

The chain is the point. A customer talks to Triage. Triage never issues
a refund and never sees one in its own tool list -- but it can hand off
to Billing, and Billing can hand off to Escalation, which can. Two hops
from the agent a customer talks to, to the agent that can move money.

No flat tool inventory shows that.
"""

from agents import Agent, function_tool, handoff


@function_tool
def lookup_order(order_id: str) -> str:
    """Read-only. The only thing Triage can actually do."""

    return "delivered"


@function_tool(name_override="issue-refund")
def refund(order_id: str, amount_cents: int) -> str:
    """Moves money."""

    return "refunded"


@function_tool
def purge_customer(customer_id: str) -> str:
    """Destructive, and wired to no agent at all.

    Deliberate. An adapter that only reads agent wiring would never see
    this function -- and an unreferenced privileged function is exactly
    what a reviewer wants told about.
    """

    return "purged"


escalation_agent = Agent(
    name="Escalation",
    instructions="Resolve disputed charges.",
    tools=[refund],
)

billing_agent = Agent(
    name="Billing",
    instructions="Handle billing questions; escalate disputes.",
    handoffs=[escalation_agent],
)

triage_agent = Agent(
    name="Triage",
    instructions="Answer the customer; route anything billing-related.",
    tools=[lookup_order],
    handoffs=[handoff(billing_agent)],
)

# NOT statically resolvable, and deliberately so: this agent's tools come
# from configuration at runtime.
router_agent = Agent(
    name="Router",
    instructions="Route by channel.",
    tools=load_channel_tools(),
)
