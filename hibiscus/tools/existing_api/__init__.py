"""
EAZR Existing API Tool Wrappers
================================
Exposes every discovered EAZR endpoint as a typed async tool function
that Hibiscus agents can call directly.

Usage:
    from hibiscus.tools.existing_api import client
    result = await client.get_policy_detail(policy_id="...", user_id="...")

All functions:
- Validate inputs against the discovery schema
- Add auth headers automatically
- Handle retries with exponential backoff
- Log every call with latency
- Return structured Dict or raise HibiscusToolError
"""

from .client import EAZRClient, HibiscusToolError

__all__ = ["EAZRClient", "HibiscusToolError"]
