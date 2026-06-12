"""Fetcher registry for pipeline architecture.

Maps dimension names to fetcher classes.
"""
from typing import Dict, Type

from .base_fetcher import BaseFetcher

# Registry: dimension_key -> Fetcher class
FETCHER_REGISTRY: Dict[str, Type[BaseFetcher]] = {}


def register_fetcher(dimension_key: str):
    """Decorator to register a fetcher class.

    Usage:
        @register_fetcher("0_basic")
        class BasicFetcher(BaseFetcher):
            ...
    """
    def decorator(cls: Type[BaseFetcher]):
        FETCHER_REGISTRY[dimension_key] = cls
        return cls
    return decorator


def get_fetcher(dimension_key: str, ticker: str) -> BaseFetcher:
    """Get a fetcher instance for the given dimension and ticker.

    Args:
        dimension_key: Dimension identifier (e.g., "0_basic")
        ticker: Stock ticker

    Returns:
        Fetcher instance

    Raises:
        KeyError: If dimension_key not registered
    """
    if dimension_key not in FETCHER_REGISTRY:
        raise KeyError(f"Fetcher not registered: {dimension_key}")

    fetcher_class = FETCHER_REGISTRY[dimension_key]
    return fetcher_class(ticker)


def list_fetchers() -> list[str]:
    """List all registered fetcher dimension keys."""
    return sorted(FETCHER_REGISTRY.keys())
