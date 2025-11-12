"""
DbopPlugin - Database Operation Plugin for SmartSwitch.

Automatically manages database connections and transactions for methods
decorated with @dbop switcher.
"""

from functools import wraps
from typing import Callable, TYPE_CHECKING
from smartswitch.plugin import BasePlugin

if TYPE_CHECKING:
    from smartswitch import Switcher


class DbopPlugin(BasePlugin):
    """
    Plugin for database operations with automatic cursor injection and transaction management.

    Features:
    - Automatic cursor injection via self.db.cursor()
    - Automatic commit on success if autocommit=True
    - Automatic rollback on exception
    - Thread-safe connection management

    Usage:
        class ArticleTypes:
            dbop = Switcher(name="types").plug(DbopPlugin())

            def __init__(self, db):
                self.db = db

            @dbop
            def add(self, name: str, cursor=None, autocommit: bool = True) -> dict:
                # Cursor automatically injected by plugin
                cursor.execute("INSERT INTO ...")
                # Autocommit handled by plugin if autocommit=True
                return result
    """

    def _wrap_handler(self, func: Callable, switcher: "Switcher") -> Callable:
        """
        Wrap database operation handler with connection and transaction management.

        Args:
            func: Handler function to wrap
            switcher: Switcher instance

        Returns:
            Wrapped function with automatic connection/transaction management
        """
        self.get_config(func.__name__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get handler instance (first arg is self)
            if not args:
                raise TypeError(f"{func.__name__}() missing required positional argument: 'self'")

            handler_instance = args[0]

            # Check if handler has db attribute
            if not hasattr(handler_instance, "db"):
                raise AttributeError(
                    f"{handler_instance.__class__.__name__} must have 'db' attribute "
                    f"for DbopPlugin to work"
                )

            db = handler_instance.db

            # Get autocommit from kwargs or use default False
            autocommit = kwargs.get("autocommit", False)

            # Inject cursor if not provided
            if "cursor" not in kwargs or kwargs["cursor"] is None:
                kwargs["cursor"] = db.cursor()

            try:
                # Call the original function with injected cursor
                result = func(*args, **kwargs)

                # Commit if autocommit is enabled
                if autocommit:
                    db.commit()

                return result

            except Exception:
                # Rollback on any exception
                try:
                    db.rollback()
                except Exception:
                    pass  # Rollback failed, but we're already in error state

                # Re-raise original exception
                raise

        return wrapper
