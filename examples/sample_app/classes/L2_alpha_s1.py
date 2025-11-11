"""
L2_alpha_s1 - Level 2 Alpha subclass 1.
"""

from typing import Optional, Dict, List, Any


class L2_alpha_s1:
    """Level 2 - Alpha subclass 1."""

    def __init__(
        self,
        name: str,
        port: int = 8080,
        host: str = "localhost",
        timeout: float = 30.0,
        config: Optional[Dict[str, Any]] = None,
        tags: List[str] = None,
        enabled: bool = True,
        max_connections: int = 100,
        retry_count: Optional[int] = None,
    ):
        self.name = name
        self.port = port
        self.host = host
        self.timeout = timeout
        self.config = config or {}
        self.tags = tags or []
        self.enabled = enabled
        self.max_connections = max_connections
        self.retry_count = retry_count
