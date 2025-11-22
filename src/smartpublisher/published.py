"""
Legacy PublishedClass placeholder.

User apps can inherit directly from smartroute.RoutedClass; this class
exists only for backward compatibility.
"""

from smartroute.core import RoutedClass


class PublishedClass(RoutedClass):
    """Deprecated shim that behaves exactly like RoutedClass."""

    def __init__(self, *args, **kwargs):
        super().__init__()
