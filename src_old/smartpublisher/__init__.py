"""
smartpublisher - Smart Publisher: CLI/API framework based on SmartSwitch.

Example:
    from smartpublisher import Publisher
    from smartswitch import Switcher

    class MyHandler:
        # If using __slots__, include 'smpublisher'
        __slots__ = ('data', 'smpublisher')
        api = Switcher(prefix='handler_')

        def __init__(self):
            self.data = {}

        @api
        def handler_add(self, key, value):
            self.data[key] = value

    class MyApp(Publisher):
        def initialize(self):
            self.handler = MyHandler()
            self.publish('handler', self.handler)

    if __name__ == "__main__":
        app = MyApp()
        app.run()
"""

from smartpublisher.publisher import Publisher
from smartpublisher.published import PublisherContext, discover_api_json

__version__ = "0.3.0"
__all__ = ["Publisher", "PublisherContext", "discover_api_json"]
