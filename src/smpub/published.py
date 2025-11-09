"""
PublishedClass - Mixin for classes that can be published by Publisher.
"""


class PublishedClass:
    """
    Mixin for classes that can be published by Publisher.

    Provides the `parent_api` slot that Publisher injects during publish().

    Example:
        class MyHandler(PublishedClass):
            __slots__ = ('data',)
            api = Switcher(prefix='my_')

            def __init__(self):
                self.data = {}

            @api
            def my_add(self, key, value):
                self.data[key] = value
                return "added"
    """

    __slots__ = ('parent_api',)
