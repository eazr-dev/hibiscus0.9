"""
Insurer Integration Registry
=============================
Maps insurer names to their integration classes.

Usage:
    from hibiscus.integrations.registry import get_integration

    integration = get_integration("Star Health")
    if integration:
        quote = await integration.get_quote(age=30, sum_insured=1000000)
"""
from typing import Dict, Optional

from hibiscus.integrations.base import InsurerIntegration
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Registry (lazy-loaded) ──────────────────────────────────────────────────
_registry: Optional[Dict[str, InsurerIntegration]] = None


def _build_registry() -> Dict[str, InsurerIntegration]:
    """Build the registry mapping normalized names → integration instances."""
    from hibiscus.integrations.star_health import star_health_integration
    from hibiscus.integrations.hdfc_ergo import hdfc_ergo_integration
    from hibiscus.integrations.icici_lombard import icici_lombard_integration

    registry: Dict[str, InsurerIntegration] = {}

    for integration in [star_health_integration, hdfc_ergo_integration, icici_lombard_integration]:
        # Register under canonical name
        registry[integration.name.lower()] = integration

    # Add common aliases
    aliases = {
        "star health": "star health and allied insurance",
        "star": "star health and allied insurance",
        "hdfc ergo": "hdfc ergo general insurance",
        "hdfc": "hdfc ergo general insurance",
        "icici lombard": "icici lombard general insurance",
        "icici": "icici lombard general insurance",
    }
    for alias, canonical in aliases.items():
        if canonical in registry:
            registry[alias] = registry[canonical]

    return registry


def get_integration(insurer_name: str) -> Optional[InsurerIntegration]:
    """
    Get the integration for an insurer by name (case-insensitive, fuzzy).

    Returns None if no integration is available for this insurer.
    """
    global _registry
    if _registry is None:
        _registry = _build_registry()

    name_lower = insurer_name.strip().lower()

    # Exact match
    if name_lower in _registry:
        return _registry[name_lower]

    # Substring match
    for key, integration in _registry.items():
        if key in name_lower or name_lower in key:
            return integration

    return None


def list_integrations() -> list:
    """List all available insurer integrations."""
    global _registry
    if _registry is None:
        _registry = _build_registry()

    seen = set()
    result = []
    for integration in _registry.values():
        if integration.name not in seen:
            seen.add(integration.name)
            result.append({
                "insurer": integration.name,
                "features": integration.supported_features,
            })
    return result
