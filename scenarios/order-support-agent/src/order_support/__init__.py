"""The Widgetworks order-support agent.

Every module here exists to make one committed artifact true. The agent
card advertises three skills; `tools` implements them. The card declares
a delegation target; `delegate` uses it. `controlloop.yaml` declares an
audit path per tool; each tool writes to the path declared for it.

This agent is deliberately over-privileged. It must never be deployed.
"""

__all__ = ["agent", "delegate", "tools"]
